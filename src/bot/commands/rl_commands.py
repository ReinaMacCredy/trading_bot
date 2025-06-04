import discord
from discord import Embed
from discord.ext import commands
import logging
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Import FinRL components
try:
    from src.training.rl_training_pipeline import RLTrainingPipeline
    from src.trading.rl_agent_manager import RLAgentManager
    FINRL_AVAILABLE = True
except ImportError:
    logger.warning("FinRL components not available")
    FINRL_AVAILABLE = False


class RLCommands(commands.Cog):
    """Discord commands for FinRL (Financial Reinforcement Learning) integration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.training_pipeline = None
        self.agent_manager = None
        self.active_training = {}  # Track active training sessions
        
        if FINRL_AVAILABLE:
            self._initialize_rl_components()
        
    def _initialize_rl_components(self):
        """Initialize FinRL components"""
        try:
            config = getattr(self.bot, 'config', {})
            exchange_client = getattr(self.bot, 'exchange_client', None)
            
            self.training_pipeline = RLTrainingPipeline(
                exchange_client=exchange_client,
                config=config.get('finrl', {}) if hasattr(config, 'get') else {}
            )
            
            self.agent_manager = RLAgentManager(
                exchange_client=exchange_client,
                config=config.get('finrl', {}) if hasattr(config, 'get') else {}
            )
            
            logger.info("FinRL components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing FinRL components: {e}")
            self.training_pipeline = None
            self.agent_manager = None


# FinRL Training Commands

async def rl_train_single(ctx, algorithm: str, timesteps: int = 50000):
    """
    Train a single RL agent
    
    Usage: /rltrain <algorithm> [timesteps]
    Example: /rltrain PPO 100000
    """
    if not FINRL_AVAILABLE:
        embed = Embed(title="❌ FinRL Not Available", color=0xff0000)
        embed.description = "FinRL components are not installed or configured."
        await ctx.send(embed=embed)
        return
    
    # Get RL commands instance
    rl_cog = ctx.bot.get_cog('RLCommands')
    if not rl_cog or not rl_cog.training_pipeline:
        embed = Embed(title="❌ RL System Not Ready", color=0xff0000)
        embed.description = "RL training system is not initialized."
        await ctx.send(embed=embed)
        return
    
    # Validate algorithm
    available_algorithms = ['PPO', 'A2C', 'SAC', 'TD3', 'DQN']
    if algorithm.upper() not in available_algorithms:
        embed = Embed(title="❌ Invalid Algorithm", color=0xff0000)
        embed.description = f"Available algorithms: {', '.join(available_algorithms)}"
        await ctx.send(embed=embed)
        return
    
    # Check if training is already in progress
    user_id = ctx.author.id
    if user_id in rl_cog.active_training:
        embed = Embed(title="⚠️ Training In Progress", color=0xffaa00)
        embed.description = "You already have a training session running. Please wait for it to complete."
        await ctx.send(embed=embed)
        return
    
    # Start training
    embed = Embed(title="🚀 Starting RL Training", color=0x00ff00)
    embed.add_field(name="Algorithm", value=algorithm.upper(), inline=True)
    embed.add_field(name="Timesteps", value=f"{timesteps:,}", inline=True)
    embed.add_field(name="Status", value="Preparing data...", inline=False)
    embed.set_footer(text="This may take several minutes. You'll be notified when complete.")
    
    status_message = await ctx.send(embed=embed)
    
    try:
        # Mark training as active
        rl_cog.active_training[user_id] = {
            'algorithm': algorithm.upper(),
            'start_time': datetime.now(),
            'status_message': status_message
        }
        
        # Prepare data
        train_df, val_df, test_df = rl_cog.training_pipeline.prepare_training_data()
        
        # Update status
        embed.set_field_at(2, name="Status", value="Training agent...", inline=False)
        await status_message.edit(embed=embed)
        
        # Train the agent
        result = rl_cog.training_pipeline.run_single_agent_training(
            algorithm=algorithm.upper(),
            train_df=train_df,
            val_df=val_df,
            total_timesteps=timesteps
        )
        
        # Training completed successfully
        training_time = datetime.now() - rl_cog.active_training[user_id]['start_time']
        
        embed = Embed(title="✅ Training Completed", color=0x00ff00)
        embed.add_field(name="Algorithm", value=algorithm.upper(), inline=True)
        embed.add_field(name="Model Name", value=result['model_name'], inline=True)
        embed.add_field(name="Training Time", value=str(training_time).split('.')[0], inline=True)
        
        # Add performance metrics
        training_perf = result.get('training_performance', {})
        validation_perf = result.get('validation_performance', {})
        
        if training_perf:
            embed.add_field(
                name="Training Performance",
                value=f"Final Reward: {training_perf.get('final_reward', 0):.4f}\n"
                      f"Avg Reward: {training_perf.get('avg_reward', 0):.4f}",
                inline=True
            )
        
        if validation_perf:
            embed.add_field(
                name="Validation Performance",
                value=f"Sharpe Ratio: {validation_perf.get('sharpe_ratio', 0):.4f}\n"
                      f"Total Return: {validation_perf.get('total_return', 0):.2%}",
                inline=True
            )
        
        embed.set_footer(text="Model saved and ready for prediction!")
        await status_message.edit(embed=embed)
        
    except Exception as e:
        # Training failed
        embed = Embed(title="❌ Training Failed", color=0xff0000)
        embed.description = f"Error: {str(e)}"
        embed.add_field(name="Algorithm", value=algorithm.upper(), inline=True)
        await status_message.edit(embed=embed)
        logger.error(f"RL training failed: {e}")
        
    finally:
        # Remove from active training
        if user_id in rl_cog.active_training:
            del rl_cog.active_training[user_id]


async def rl_train_ensemble(ctx, algorithms: str = "PPO,A2C,SAC"):
    """
    Train an ensemble of RL agents
    
    Usage: /rlensemble [algorithms]
    Example: /rlensemble PPO,A2C,SAC,TD3
    """
    if not FINRL_AVAILABLE:
        embed = Embed(title="❌ FinRL Not Available", color=0xff0000)
        embed.description = "FinRL components are not installed or configured."
        await ctx.send(embed=embed)
        return
    
    # Get RL commands instance
    rl_cog = ctx.bot.get_cog('RLCommands')
    if not rl_cog or not rl_cog.training_pipeline:
        embed = Embed(title="❌ RL System Not Ready", color=0xff0000)
        embed.description = "RL training system is not initialized."
        await ctx.send(embed=embed)
        return
    
    # Parse algorithms
    algorithm_list = [alg.strip().upper() for alg in algorithms.split(',')]
    available_algorithms = ['PPO', 'A2C', 'SAC', 'TD3', 'DQN']
    
    invalid_algorithms = [alg for alg in algorithm_list if alg not in available_algorithms]
    if invalid_algorithms:
        embed = Embed(title="❌ Invalid Algorithms", color=0xff0000)
        embed.description = f"Invalid: {', '.join(invalid_algorithms)}\n"
        embed.description += f"Available: {', '.join(available_algorithms)}"
        await ctx.send(embed=embed)
        return
    
    # Check if training is already in progress
    user_id = ctx.author.id
    if user_id in rl_cog.active_training:
        embed = Embed(title="⚠️ Training In Progress", color=0xffaa00)
        embed.description = "You already have a training session running."
        await ctx.send(embed=embed)
        return
    
    # Start ensemble training
    embed = Embed(title="🎯 Starting Ensemble Training", color=0x00ff00)
    embed.add_field(name="Algorithms", value=', '.join(algorithm_list), inline=False)
    embed.add_field(name="Total Models", value=str(len(algorithm_list)), inline=True)
    embed.add_field(name="Status", value="Preparing data...", inline=False)
    embed.set_footer(text="This will take longer than single agent training.")
    
    status_message = await ctx.send(embed=embed)
    
    try:
        # Mark training as active
        rl_cog.active_training[user_id] = {
            'type': 'ensemble',
            'algorithms': algorithm_list,
            'start_time': datetime.now(),
            'status_message': status_message
        }
        
        # Update status
        embed.set_field_at(2, name="Status", value="Training ensemble...", inline=False)
        await status_message.edit(embed=embed)
        
        # Train ensemble
        result = rl_cog.training_pipeline.run_ensemble_training(
            algorithms=algorithm_list
        )
        
        # Training completed
        training_time = datetime.now() - rl_cog.active_training[user_id]['start_time']
        
        embed = Embed(title="✅ Ensemble Training Completed", color=0x00ff00)
        embed.add_field(name="Ensemble Name", value=result['ensemble_name'], inline=True)
        embed.add_field(name="Models Trained", value=f"{result['total_models']}/{len(algorithm_list)}", inline=True)
        embed.add_field(name="Training Time", value=str(training_time).split('.')[0], inline=True)
        
        # Show results for each algorithm
        results_text = ""
        for alg, alg_result in result['results'].items():
            val_perf = alg_result.get('validation_performance', {})
            sharpe = val_perf.get('sharpe_ratio', 0)
            returns = val_perf.get('total_return', 0)
            results_text += f"{alg}: Sharpe {sharpe:.3f}, Return {returns:.2%}\n"
        
        if results_text:
            embed.add_field(name="Algorithm Performance", value=results_text, inline=False)
        
        embed.set_footer(text="Ensemble ready for prediction!")
        await status_message.edit(embed=embed)
        
    except Exception as e:
        embed = Embed(title="❌ Ensemble Training Failed", color=0xff0000)
        embed.description = f"Error: {str(e)}"
        await status_message.edit(embed=embed)
        logger.error(f"Ensemble training failed: {e}")
        
    finally:
        if user_id in rl_cog.active_training:
            del rl_cog.active_training[user_id]


async def rl_predict(ctx, model_name: str = None, symbol: str = "BTC/USDT"):
    """
    Get RL agent prediction for trading
    
    Usage: /rlpredict [model_name] [symbol]
    Example: /rlpredict PPO_20241201_143000 ETH/USDT
    """
    if not FINRL_AVAILABLE:
        embed = Embed(title="❌ FinRL Not Available", color=0xff0000)
        embed.description = "FinRL components are not installed or configured."
        await ctx.send(embed=embed)
        return
    
    rl_cog = ctx.bot.get_cog('RLCommands')
    if not rl_cog or not rl_cog.agent_manager:
        embed = Embed(title="❌ RL System Not Ready", color=0xff0000)
        embed.description = "RL agent system is not initialized."
        await ctx.send(embed=embed)
        return
    
    try:
        # If no model specified, use best model
        if model_name is None:
            model_name = rl_cog.agent_manager.best_model
            
        if model_name is None:
            embed = Embed(title="❌ No Models Available", color=0xff0000)
            embed.description = "No trained models found. Train a model first with `/rltrain`"
            await ctx.send(embed=embed)
            return
        
        # Get current market data
        if ctx.bot.exchange_client:
            # Fetch recent data for prediction
            current_data = await _fetch_prediction_data(ctx.bot.exchange_client, symbol)
        else:
            embed = Embed(title="❌ Exchange Not Available", color=0xff0000)
            embed.description = "Exchange client not configured."
            await ctx.send(embed=embed)
            return
        
        # Get prediction
        action, prediction_info = rl_cog.agent_manager.predict_action(
            model_name=model_name,
            current_data=current_data
        )
        
        # Format prediction result
        embed = Embed(title="🤖 RL Agent Prediction", color=0x0099ff)
        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Model", value=model_name, inline=True)
        embed.add_field(name="Algorithm", value=prediction_info.get('algorithm', 'Unknown'), inline=True)
        
        # Interpret action
        action_value = float(action[0]) if len(action) > 0 else 0
        
        if action_value > 0.1:
            action_text = f"🟢 **BUY** (Strength: {action_value:.2f})"
            color = 0x00ff00
        elif action_value < -0.1:
            action_text = f"🔴 **SELL** (Strength: {abs(action_value):.2f})"
            color = 0xff0000
        else:
            action_text = f"⚪ **HOLD** (Neutral: {action_value:.2f})"
            color = 0xffaa00
        
        embed.color = color
        embed.add_field(name="Action", value=action_text, inline=False)
        embed.add_field(name="Confidence", value=f"{prediction_info.get('confidence', 0.5):.2f}", inline=True)
        embed.add_field(name="Timestamp", value=prediction_info['timestamp'].strftime('%H:%M:%S'), inline=True)
        
        embed.set_footer(text="⚠️ This is AI-generated advice. Trade at your own risk!")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = Embed(title="❌ Prediction Failed", color=0xff0000)
        embed.description = f"Error: {str(e)}"
        await ctx.send(embed=embed)
        logger.error(f"RL prediction failed: {e}")


async def rl_ensemble_predict(ctx, ensemble_name: str = None, symbol: str = "BTC/USDT"):
    """
    Get ensemble prediction from multiple RL agents
    
    Usage: /rlensemblepredict [ensemble_name] [symbol]
    Example: /rlensemblepredict ensemble_20241201 ETH/USDT
    """
    if not FINRL_AVAILABLE:
        embed = Embed(title="❌ FinRL Not Available", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    rl_cog = ctx.bot.get_cog('RLCommands')
    if not rl_cog or not rl_cog.agent_manager:
        embed = Embed(title="❌ RL System Not Ready", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    try:
        # Find ensemble if not specified
        if ensemble_name is None and rl_cog.agent_manager.ensemble_models:
            ensemble_name = rl_cog.agent_manager.ensemble_models[-1]['name']  # Latest ensemble
            
        if ensemble_name is None:
            embed = Embed(title="❌ No Ensembles Available", color=0xff0000)
            embed.description = "No ensemble models found. Train an ensemble first with `/rlensemble`"
            await ctx.send(embed=embed)
            return
        
        # Get current market data
        if ctx.bot.exchange_client:
            current_data = await _fetch_prediction_data(ctx.bot.exchange_client, symbol)
        else:
            embed = Embed(title="❌ Exchange Not Available", color=0xff0000)
            await ctx.send(embed=embed)
            return
        
        # Get ensemble prediction
        action, prediction_info = rl_cog.agent_manager.get_ensemble_prediction(
            ensemble_name=ensemble_name,
            current_data=current_data,
            voting_method='weighted'
        )
        
        # Format prediction result
        embed = Embed(title="🎯 Ensemble Prediction", color=0x9933ff)
        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Ensemble", value=ensemble_name, inline=True)
        embed.add_field(name="Models", value=str(prediction_info.get('num_models', 0)), inline=True)
        
        # Interpret ensemble action
        action_value = float(action[0]) if len(action) > 0 else 0
        
        if action_value > 0.1:
            action_text = f"🟢 **BUY** (Strength: {action_value:.2f})"
            color = 0x00ff00
        elif action_value < -0.1:
            action_text = f"🔴 **SELL** (Strength: {abs(action_value):.2f})"
            color = 0xff0000
        else:
            action_text = f"⚪ **HOLD** (Neutral: {action_value:.2f})"
            color = 0xffaa00
        
        embed.color = color
        embed.add_field(name="Ensemble Action", value=action_text, inline=False)
        embed.add_field(name="Voting Method", value=prediction_info.get('voting_method', 'average'), inline=True)
        embed.add_field(name="Timestamp", value=prediction_info['timestamp'].strftime('%H:%M:%S'), inline=True)
        
        # Show contributing models
        models_text = ', '.join(prediction_info.get('model_predictions', []))
        if models_text:
            embed.add_field(name="Contributing Models", value=models_text, inline=False)
        
        embed.set_footer(text="⚠️ Ensemble prediction. Trade responsibly!")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = Embed(title="❌ Ensemble Prediction Failed", color=0xff0000)
        embed.description = f"Error: {str(e)}"
        await ctx.send(embed=embed)
        logger.error(f"Ensemble prediction failed: {e}")


async def rl_models(ctx):
    """
    List all trained RL models
    
    Usage: /rlmodels
    """
    if not FINRL_AVAILABLE:
        embed = Embed(title="❌ FinRL Not Available", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    rl_cog = ctx.bot.get_cog('RLCommands')
    if not rl_cog or not rl_cog.agent_manager:
        embed = Embed(title="❌ RL System Not Ready", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    try:
        summary = rl_cog.agent_manager.get_model_summary()
        
        embed = Embed(title="🤖 Trained RL Models", color=0x0099ff)
        embed.add_field(name="Total Models", value=summary['total_models'], inline=True)
        embed.add_field(name="Algorithms", value=', '.join(summary['algorithms_used']), inline=True)
        embed.add_field(name="Ensembles", value=summary['ensembles'], inline=True)
        
        if summary['best_model']:
            embed.add_field(name="Best Model", value=summary['best_model'], inline=False)
        
        # List individual models
        if summary['models']:
            models_text = ""
            for name, info in list(summary['models'].items())[:10]:  # Show max 10 models
                algo = info['algorithm']
                training_time = info['training_time']
                models_text += f"• **{name}** ({algo}) - {training_time}\n"
            
            if len(summary['models']) > 10:
                models_text += f"... and {len(summary['models']) - 10} more models"
            
            embed.add_field(name="Available Models", value=models_text or "None", inline=False)
        
        # List ensembles
        if rl_cog.agent_manager.ensemble_models:
            ensemble_text = ""
            for ensemble in rl_cog.agent_manager.ensemble_models:
                name = ensemble['name']
                algorithms = ', '.join(ensemble['algorithms'])
                ensemble_text += f"• **{name}** ({algorithms})\n"
            
            embed.add_field(name="Ensembles", value=ensemble_text, inline=False)
        
        embed.set_footer(text="Use /rlpredict <model_name> to get predictions")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = Embed(title="❌ Error Loading Models", color=0xff0000)
        embed.description = f"Error: {str(e)}"
        await ctx.send(embed=embed)


async def rl_status(ctx):
    """
    Show RL training status
    
    Usage: /rlstatus
    """
    if not FINRL_AVAILABLE:
        embed = Embed(title="❌ FinRL Not Available", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    rl_cog = ctx.bot.get_cog('RLCommands')
    if not rl_cog:
        embed = Embed(title="❌ RL System Not Ready", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    embed = Embed(title="📊 RL System Status", color=0x0099ff)
    
    # System status
    training_pipeline_status = "✅ Ready" if rl_cog.training_pipeline else "❌ Not Available"
    agent_manager_status = "✅ Ready" if rl_cog.agent_manager else "❌ Not Available"
    
    embed.add_field(name="Training Pipeline", value=training_pipeline_status, inline=True)
    embed.add_field(name="Agent Manager", value=agent_manager_status, inline=True)
    embed.add_field(name="FinRL Library", value="✅ Available" if FINRL_AVAILABLE else "❌ Not Available", inline=True)
    
    # Active training sessions
    active_count = len(rl_cog.active_training)
    embed.add_field(name="Active Training Sessions", value=str(active_count), inline=True)
    
    if rl_cog.active_training:
        active_text = ""
        for user_id, session in rl_cog.active_training.items():
            session_type = session.get('type', 'single')
            algorithm = session.get('algorithm', session.get('algorithms', 'Unknown'))
            start_time = session['start_time']
            duration = datetime.now() - start_time
            active_text += f"• <@{user_id}>: {session_type} ({algorithm}) - {str(duration).split('.')[0]}\n"
        
        embed.add_field(name="Current Sessions", value=active_text, inline=False)
    
    # Model statistics
    if rl_cog.agent_manager:
        summary = rl_cog.agent_manager.get_model_summary()
        embed.add_field(name="Total Models", value=summary['total_models'], inline=True)
        embed.add_field(name="Best Model", value=summary.get('best_model', 'None'), inline=True)
    
    await ctx.send(embed=embed)


async def rl_help(ctx):
    """
    Show RL commands help
    
    Usage: /rlhelp
    """
    embed = Embed(title="🤖 FinRL Commands Help", color=0x0099ff)
    embed.description = "Financial Reinforcement Learning integration for advanced AI trading"
    
    # Training commands
    training_commands = """
    `/rltrain <algorithm> [timesteps]` - Train single RL agent
    `/rlensemble [algorithms]` - Train ensemble of agents
    `/rloptimize <algorithm>` - Optimize hyperparameters
    """
    embed.add_field(name="🏋️ Training Commands", value=training_commands, inline=False)
    
    # Prediction commands
    prediction_commands = """
    `/rlpredict [model] [symbol]` - Get single model prediction
    `/rlensemblepredict [ensemble] [symbol]` - Get ensemble prediction
    """
    embed.add_field(name="🔮 Prediction Commands", value=prediction_commands, inline=False)
    
    # Management commands
    management_commands = """
    `/rlmodels` - List all trained models
    `/rlstatus` - Show system status
    `/rlhelp` - Show this help
    """
    embed.add_field(name="⚙️ Management Commands", value=management_commands, inline=False)
    
    # Available algorithms
    algorithms = "PPO, A2C, SAC, TD3, DQN, TQC, ARS"
    embed.add_field(name="🧠 Available Algorithms", value=algorithms, inline=False)
    
    # Examples
    examples = """
    `/rltrain PPO 100000` - Train PPO agent with 100k timesteps
    `/rlensemble PPO,A2C,SAC` - Train ensemble with 3 algorithms
    `/rlpredict best_model BTC/USDT` - Get prediction for BTC/USDT
    """
    embed.add_field(name="💡 Examples", value=examples, inline=False)
    
    embed.set_footer(text="⚠️ RL training requires significant computation time and resources")
    await ctx.send(embed=embed)


# Helper functions

async def _fetch_prediction_data(exchange_client, symbol: str) -> dict:
    """Fetch recent market data for prediction"""
    try:
        # Fetch recent OHLCV data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days for context
        
        data = exchange_client.get_historical_data(
            symbol=symbol,
            timeframe='1h',
            start_date=start_date,
            end_date=end_date
        )
        
        if data:
            import pandas as pd
            df = pd.DataFrame(data)
            df['symbol'] = symbol
            return df
        else:
            raise ValueError(f"No data available for {symbol}")
            
    except Exception as e:
        logger.error(f"Error fetching prediction data: {e}")
        raise


# Register command functions
async def setup_rl_commands(bot):
    """Setup RL commands"""
    # Add the cog
    await bot.add_cog(RLCommands(bot))
    
    # Register individual command functions
    bot.command(name='rltrain')(rl_train_single)
    bot.command(name='rlensemble')(rl_train_ensemble) 
    bot.command(name='rlpredict')(rl_predict)
    bot.command(name='rlensemblepredict')(rl_ensemble_predict)
    bot.command(name='rlmodels')(rl_models)
    bot.command(name='rlstatus')(rl_status)
    bot.command(name='rlhelp')(rl_help) 