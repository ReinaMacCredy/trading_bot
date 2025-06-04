import logging
import pandas as pd
import numpy as np
import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import time
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    logger.warning("Weights & Biases not available. Training tracking disabled.")
    WANDB_AVAILABLE = False

# Import FinRL and RL components
try:
    from stable_baselines3.common.evaluation import evaluate_policy
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.monitor import Monitor
    SB3_AVAILABLE = True
except ImportError:
    logger.warning("Stable Baselines3 not available. Training pipeline disabled.")
    SB3_AVAILABLE = False

from src.trading.rl_agent_manager import RLAgentManager
from src.trading.finrl_environment import CryptoTradingEnv, FinRLDataProcessor


class RLTrainingPipeline:
    """
    Automated training pipeline for FinRL reinforcement learning agents.
    Handles data preparation, multi-agent training, evaluation, and model selection.
    """
    
    def __init__(self, 
                 exchange_client=None,
                 config: Dict[str, Any] = None,
                 output_dir: str = 'training_results'):
        """
        Initialize the RL Training Pipeline.
        
        Args:
            exchange_client: Exchange client for fetching market data
            config: Configuration dictionary
            output_dir: Directory for saving training results
        """
        self.exchange_client = exchange_client
        self.config = config or {}
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.rl_manager = RLAgentManager(
            exchange_client=exchange_client,
            config=config
        )
        
        # Training configuration
        self.training_config = {
            'symbols': config.get('symbols', ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']),
            'timeframe': config.get('timeframe', '1h'),
            'training_days': config.get('training_days', 365),
            'validation_days': config.get('validation_days', 60),
            'test_days': config.get('test_days', 30),
            'agents_to_train': config.get('agents_to_train', ['PPO', 'A2C', 'SAC']),
            'timesteps_per_agent': config.get('timesteps_per_agent', 50000),
            'eval_episodes': config.get('eval_episodes', 10),
            'min_performance_threshold': config.get('min_performance_threshold', 0.05)
        }
        
        # Results tracking
        self.training_results = {}
        self.evaluation_results = {}
        self.best_agents = {}
        
        logger.info("RL Training Pipeline initialized")
        
    def prepare_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Prepare training, validation, and test datasets.
        
        Returns:
            Dictionary with 'train', 'validation', and 'test' DataFrames
        """
        try:
            logger.info("Preparing datasets for RL training...")
            
            # Calculate date ranges
            end_date = datetime.now()
            test_start = end_date - timedelta(days=self.training_config['test_days'])
            val_start = test_start - timedelta(days=self.training_config['validation_days'])
            train_start = val_start - timedelta(days=self.training_config['training_days'])
            
            logger.info(f"Training period: {train_start.date()} to {val_start.date()}")
            logger.info(f"Validation period: {val_start.date()} to {test_start.date()}")
            logger.info(f"Test period: {test_start.date()} to {end_date.date()}")
            
            # Fetch complete dataset
            all_data = self.rl_manager.prepare_training_data(
                symbols=self.training_config['symbols'],
                timeframe=self.training_config['timeframe'],
                days=self.training_config['training_days'] + 
                     self.training_config['validation_days'] + 
                     self.training_config['test_days']
            )
            
            if all_data.empty:
                raise ValueError("Failed to fetch market data")
            
            # Convert date column to datetime if it's not already
            if 'date' in all_data.columns:
                all_data['date'] = pd.to_datetime(all_data['date'])
            
            # Split into datasets
            datasets = {}
            
            # Training set
            train_mask = all_data['date'] < val_start
            datasets['train'] = all_data[train_mask].reset_index(drop=True)
            
            # Validation set
            val_mask = (all_data['date'] >= val_start) & (all_data['date'] < test_start)
            datasets['validation'] = all_data[val_mask].reset_index(drop=True)
            
            # Test set
            test_mask = all_data['date'] >= test_start
            datasets['test'] = all_data[test_mask].reset_index(drop=True)
            
            # Log dataset sizes
            for name, df in datasets.items():
                logger.info(f"{name.capitalize()} dataset: {len(df)} rows")
            
            # Save datasets
            for name, df in datasets.items():
                filepath = os.path.join(self.output_dir, f'{name}_dataset.csv')
                df.to_csv(filepath, index=False)
                logger.info(f"Saved {name} dataset to {filepath}")
            
            return datasets
            
        except Exception as e:
            logger.error(f"Error preparing datasets: {e}")
            return {}
    
    def train_all_agents(self, 
                        train_data: pd.DataFrame,
                        validation_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train all specified agents with the training data.
        
        Args:
            train_data: Training dataset
            validation_data: Validation dataset
            
        Returns:
            Dictionary with training results for each agent
        """
        try:
            logger.info(f"Training {len(self.training_config['agents_to_train'])} agents...")
            
            training_results = {}
            
            for agent_type in self.training_config['agents_to_train']:
                logger.info(f"Training {agent_type} agent...")
                
                start_time = time.time()
                
                # Train the agent
                success = self.rl_manager.train_agent(
                    agent_type=agent_type,
                    df=train_data,
                    total_timesteps=self.training_config['timesteps_per_agent']
                )
                
                training_time = time.time() - start_time
                
                if success:
                    # Evaluate on validation data
                    val_results = self.evaluate_agent(
                        agent_type=agent_type,
                        test_data=validation_data,
                        num_episodes=self.training_config['eval_episodes']
                    )
                    
                    training_results[agent_type] = {
                        'success': True,
                        'training_time': training_time,
                        'validation_results': val_results,
                        'timesteps': self.training_config['timesteps_per_agent']
                    }
                    
                    logger.info(f"{agent_type} training completed successfully in {training_time:.2f}s")
                    logger.info(f"Validation performance: {val_results}")
                    
                else:
                    training_results[agent_type] = {
                        'success': False,
                        'training_time': training_time,
                        'error': 'Training failed'
                    }
                    logger.error(f"{agent_type} training failed")
            
            self.training_results = training_results
            
            # Save training results
            results_path = os.path.join(self.output_dir, 'training_results.json')
            with open(results_path, 'w') as f:
                json.dump(self._serialize_results(training_results), f, indent=2)
            
            return training_results
            
        except Exception as e:
            logger.error(f"Error training agents: {e}")
            return {}
    
    def evaluate_agent(self, 
                      agent_type: str,
                      test_data: pd.DataFrame,
                      num_episodes: int = 10) -> Dict[str, float]:
        """
        Evaluate a trained agent on test data.
        
        Args:
            agent_type: Type of agent to evaluate
            test_data: Test dataset
            num_episodes: Number of episodes to run
            
        Returns:
            Dictionary with evaluation metrics
        """
        try:
            if agent_type not in self.rl_manager.trained_agents:
                logger.error(f"Agent {agent_type} not trained")
                return {}
            
            logger.info(f"Evaluating {agent_type} agent...")
            
            # Create test environment
            test_env = self.rl_manager.create_trading_environment(
                df=test_data,
                initial_amount=10000,
                transaction_cost_pct=0.001
            )
            
            if test_env is None:
                return {}
            
            # Wrap environment
            test_env = Monitor(test_env)
            test_env = DummyVecEnv([lambda: test_env])
            
            # Get trained model
            model = self.rl_manager.trained_agents[agent_type]['model']
            
            # Evaluate policy
            mean_reward, std_reward = evaluate_policy(
                model, 
                test_env, 
                n_eval_episodes=num_episodes,
                deterministic=True
            )
            
            # Run single episode for detailed analysis
            obs = test_env.reset()
            episode_rewards = []
            portfolio_values = []
            actions_taken = []
            done = False
            
            while not done:
                action, _states = model.predict(obs, deterministic=True)
                obs, reward, done, info = test_env.step(action)
                
                episode_rewards.append(reward[0])  # DummyVecEnv returns arrays
                actions_taken.append(action[0])
                
                if len(info) > 0 and 'portfolio_value' in info[0]:
                    portfolio_values.append(info[0]['portfolio_value'])
            
            # Calculate performance metrics
            total_reward = sum(episode_rewards)
            
            if portfolio_values and len(portfolio_values) > 1:
                initial_value = portfolio_values[0]
                final_value = portfolio_values[-1]
                total_return = (final_value - initial_value) / initial_value
                
                # Calculate Sharpe ratio
                returns = np.diff(portfolio_values) / np.array(portfolio_values[:-1])
                returns = returns[np.isfinite(returns)]  # Remove inf/nan
                
                if len(returns) > 1 and np.std(returns) > 0:
                    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
                else:
                    sharpe_ratio = 0.0
                
                # Maximum drawdown
                peak = np.maximum.accumulate(portfolio_values)
                drawdown = (np.array(peak) - np.array(portfolio_values)) / np.array(peak)
                max_drawdown = np.max(drawdown)
                
                # Win rate (positive returns)
                positive_returns = np.sum(returns > 0)
                win_rate = positive_returns / len(returns) if len(returns) > 0 else 0
                
            else:
                total_return = 0.0
                sharpe_ratio = 0.0
                max_drawdown = 0.0
                win_rate = 0.0
            
            # Calculate action distribution
            action_stats = {
                'mean_action': np.mean(actions_taken),
                'std_action': np.std(actions_taken),
                'min_action': np.min(actions_taken),
                'max_action': np.max(actions_taken)
            }
            
            evaluation_results = {
                'mean_reward': float(mean_reward),
                'std_reward': float(std_reward),
                'total_return': float(total_return),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'win_rate': float(win_rate),
                'num_episodes': num_episodes,
                'episode_length': len(episode_rewards),
                'action_stats': action_stats
            }
            
            logger.info(f"{agent_type} evaluation completed:")
            logger.info(f"  Mean reward: {mean_reward:.4f} ± {std_reward:.4f}")
            logger.info(f"  Total return: {total_return:.2%}")
            logger.info(f"  Sharpe ratio: {sharpe_ratio:.4f}")
            logger.info(f"  Max drawdown: {max_drawdown:.2%}")
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error evaluating {agent_type}: {e}")
            return {}
    
    def evaluate_all_agents(self, test_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Evaluate all trained agents on test data.
        
        Args:
            test_data: Test dataset
            
        Returns:
            Dictionary with evaluation results for each agent
        """
        try:
            logger.info("Evaluating all trained agents...")
            
            evaluation_results = {}
            
            for agent_type in self.rl_manager.trained_agents.keys():
                results = self.evaluate_agent(
                    agent_type=agent_type,
                    test_data=test_data,
                    num_episodes=self.training_config['eval_episodes']
                )
                
                if results:
                    evaluation_results[agent_type] = results
            
            self.evaluation_results = evaluation_results
            
            # Save evaluation results
            results_path = os.path.join(self.output_dir, 'evaluation_results.json')
            with open(results_path, 'w') as f:
                json.dump(evaluation_results, f, indent=2)
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error evaluating all agents: {e}")
            return {}
    
    def select_best_agents(self, 
                          evaluation_results: Dict[str, Dict[str, float]],
                          primary_metric: str = 'sharpe_ratio',
                          secondary_metric: str = 'total_return') -> Dict[str, Any]:
        """
        Select the best performing agents based on evaluation metrics.
        
        Args:
            evaluation_results: Results from agent evaluation
            primary_metric: Primary metric for selection
            secondary_metric: Secondary metric for tie-breaking
            
        Returns:
            Dictionary with best agent information
        """
        try:
            if not evaluation_results:
                logger.warning("No evaluation results available for agent selection")
                return {}
            
            logger.info(f"Selecting best agents based on {primary_metric}")
            
            # Filter agents that meet minimum performance threshold
            qualified_agents = {}
            for agent_type, results in evaluation_results.items():
                if results.get(primary_metric, 0) >= self.training_config['min_performance_threshold']:
                    qualified_agents[agent_type] = results
            
            if not qualified_agents:
                logger.warning("No agents meet the minimum performance threshold")
                # Use all agents if none meet threshold
                qualified_agents = evaluation_results
            
            # Sort agents by primary metric
            sorted_agents = sorted(
                qualified_agents.items(),
                key=lambda x: (x[1].get(primary_metric, 0), x[1].get(secondary_metric, 0)),
                reverse=True
            )
            
            # Select top agents
            best_agent = sorted_agents[0]
            best_agents_info = {
                'best_overall': {
                    'agent_type': best_agent[0],
                    'metrics': best_agent[1]
                },
                'rankings': []
            }
            
            # Add rankings for all agents
            for i, (agent_type, metrics) in enumerate(sorted_agents):
                best_agents_info['rankings'].append({
                    'rank': i + 1,
                    'agent_type': agent_type,
                    'primary_metric_value': metrics.get(primary_metric, 0),
                    'secondary_metric_value': metrics.get(secondary_metric, 0),
                    'all_metrics': metrics
                })
            
            # Find best agent for each metric
            for metric in ['sharpe_ratio', 'total_return', 'win_rate', 'mean_reward']:
                if metric in qualified_agents[sorted_agents[0][0]]:
                    best_for_metric = max(
                        qualified_agents.items(),
                        key=lambda x: x[1].get(metric, 0)
                    )
                    best_agents_info[f'best_{metric}'] = {
                        'agent_type': best_for_metric[0],
                        'value': best_for_metric[1][metric]
                    }
            
            # Calculate ensemble weights based on performance
            total_performance = sum(
                results.get(primary_metric, 0) for results in qualified_agents.values()
            )
            
            if total_performance > 0:
                ensemble_weights = {
                    agent_type: max(0.1, results.get(primary_metric, 0) / total_performance)
                    for agent_type, results in qualified_agents.items()
                }
                
                # Normalize weights
                weight_sum = sum(ensemble_weights.values())
                ensemble_weights = {
                    agent: weight / weight_sum 
                    for agent, weight in ensemble_weights.items()
                }
                
                best_agents_info['ensemble_weights'] = ensemble_weights
            
            self.best_agents = best_agents_info
            
            # Save best agents info
            best_agents_path = os.path.join(self.output_dir, 'best_agents.json')
            with open(best_agents_path, 'w') as f:
                json.dump(best_agents_info, f, indent=2)
            
            logger.info(f"Best agent: {best_agents_info['best_overall']['agent_type']}")
            logger.info(f"Best {primary_metric}: {best_agents_info['best_overall']['metrics'][primary_metric]:.4f}")
            
            return best_agents_info
            
        except Exception as e:
            logger.error(f"Error selecting best agents: {e}")
            return {}
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete training pipeline.
        
        Returns:
            Dictionary with complete pipeline results
        """
        try:
            logger.info("Starting RL training pipeline...")
            start_time = time.time()
            
            # Step 1: Prepare datasets
            logger.info("Step 1: Preparing datasets...")
            datasets = self.prepare_datasets()
            if not datasets:
                raise ValueError("Failed to prepare datasets")
            
            # Step 2: Train all agents
            logger.info("Step 2: Training agents...")
            training_results = self.train_all_agents(
                train_data=datasets['train'],
                validation_data=datasets['validation']
            )
            
            if not training_results:
                raise ValueError("Failed to train agents")
            
            # Step 3: Evaluate all agents
            logger.info("Step 3: Evaluating agents...")
            evaluation_results = self.evaluate_all_agents(
                test_data=datasets['test']
            )
            
            if not evaluation_results:
                logger.warning("No agents to evaluate")
            
            # Step 4: Select best agents
            logger.info("Step 4: Selecting best agents...")
            best_agents = self.select_best_agents(evaluation_results)
            
            # Step 5: Update ensemble weights
            if best_agents and 'ensemble_weights' in best_agents:
                logger.info("Step 5: Updating ensemble weights...")
                self.rl_manager.update_ensemble_weights(best_agents['ensemble_weights'])
                self.rl_manager.save_manager_state()
            
            total_time = time.time() - start_time
            
            # Compile final results
            pipeline_results = {
                'pipeline_completed': True,
                'total_time': total_time,
                'datasets_prepared': len(datasets),
                'agents_trained': len([r for r in training_results.values() if r.get('success', False)]),
                'agents_evaluated': len(evaluation_results),
                'training_results': training_results,
                'evaluation_results': evaluation_results,
                'best_agents': best_agents,
                'completion_time': datetime.now().isoformat()
            }
            
            # Save complete results
            pipeline_path = os.path.join(self.output_dir, 'pipeline_results.json')
            with open(pipeline_path, 'w') as f:
                json.dump(self._serialize_results(pipeline_results), f, indent=2)
            
            logger.info(f"RL training pipeline completed successfully in {total_time:.2f}s")
            logger.info(f"Trained {pipeline_results['agents_trained']} agents successfully")
            logger.info(f"Results saved to {self.output_dir}")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"RL training pipeline failed: {e}")
            return {
                'pipeline_completed': False,
                'error': str(e),
                'completion_time': datetime.now().isoformat()
            }
    
    def _serialize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize results for JSON storage.
        
        Args:
            results: Results dictionary
            
        Returns:
            Serialized results
        """
        def convert_item(item):
            if isinstance(item, (np.integer, np.floating)):
                return float(item)
            elif isinstance(item, np.ndarray):
                return item.tolist()
            elif isinstance(item, datetime):
                return item.isoformat()
            elif isinstance(item, dict):
                return {k: convert_item(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [convert_item(i) for i in item]
            else:
                return item
        
        return convert_item(results)
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive training report.
        
        Returns:
            Formatted report string
        """
        try:
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("FinRL Training Pipeline Report")
            report_lines.append("=" * 60)
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # Training configuration
            report_lines.append("Training Configuration:")
            report_lines.append("-" * 25)
            for key, value in self.training_config.items():
                report_lines.append(f"{key}: {value}")
            report_lines.append("")
            
            # Training results
            if self.training_results:
                report_lines.append("Training Results:")
                report_lines.append("-" * 17)
                for agent_type, results in self.training_results.items():
                    if results.get('success', False):
                        report_lines.append(f"✅ {agent_type}: {results['training_time']:.2f}s")
                    else:
                        report_lines.append(f"❌ {agent_type}: FAILED")
                report_lines.append("")
            
            # Evaluation results
            if self.evaluation_results:
                report_lines.append("Evaluation Results:")
                report_lines.append("-" * 19)
                report_lines.append(f"{'Agent':<8} {'Sharpe':<8} {'Return':<8} {'Drawdown':<10} {'Win Rate':<8}")
                report_lines.append("-" * 50)
                
                for agent_type, results in self.evaluation_results.items():
                    sharpe = results.get('sharpe_ratio', 0)
                    total_return = results.get('total_return', 0)
                    max_dd = results.get('max_drawdown', 0)
                    win_rate = results.get('win_rate', 0)
                    
                    report_lines.append(
                        f"{agent_type:<8} {sharpe:<8.3f} {total_return:<8.2%} "
                        f"{max_dd:<10.2%} {win_rate:<8.2%}"
                    )
                report_lines.append("")
            
            # Best agents
            if self.best_agents:
                best_overall = self.best_agents.get('best_overall', {})
                if best_overall:
                    report_lines.append("Best Agent:")
                    report_lines.append("-" * 11)
                    report_lines.append(f"Agent: {best_overall['agent_type']}")
                    
                    metrics = best_overall.get('metrics', {})
                    for metric, value in metrics.items():
                        if isinstance(value, float):
                            report_lines.append(f"{metric}: {value:.4f}")
                        else:
                            report_lines.append(f"{metric}: {value}")
                    
                    report_lines.append("")
                
                # Ensemble weights
                weights = self.best_agents.get('ensemble_weights', {})
                if weights:
                    report_lines.append("Ensemble Weights:")
                    report_lines.append("-" * 17)
                    for agent, weight in weights.items():
                        report_lines.append(f"{agent}: {weight:.2%}")
                    report_lines.append("")
            
            report_lines.append("=" * 60)
            
            report_text = "\n".join(report_lines)
            
            # Save report
            report_path = os.path.join(self.output_dir, 'training_report.txt')
            with open(report_path, 'w') as f:
                f.write(report_text)
            
            logger.info(f"Training report saved to {report_path}")
            
            return report_text
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}" 