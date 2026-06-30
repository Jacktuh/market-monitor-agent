#!/usr/bin/env python3
"""
Market Monitor Agent

Main orchestrator that:
1. Fetches market data at regular intervals
2. Runs rule evaluations
3. Triggers alerts and actions
"""

import time
import logging
from datetime import datetime
from stock_price_fetcher import StockPriceFetcher
from rules_engine import RulesEngine, Signal, print_evaluations
from config import (
    DATA_REFRESH_INTERVAL_SECONDS,
    RULE_CHECK_INTERVAL_SECONDS,
    TICKERS,
    ALERTS_ENABLED,
    LOG_FILE,
    LOG_LEVEL,
)


class MarketMonitorAgent:
    """Main agent for monitoring markets and executing rules"""

    def __init__(self):
        self.fetcher = StockPriceFetcher()
        self.engine = RulesEngine()
        self.setup_logging()
        self.current_data = {}
        self.last_data_refresh = None
        self.last_rule_check = None
        self.positions = {}  # Track current positions

    def setup_logging(self):
        """Configure logging"""
        import os

        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def fetch_market_data(self):
        """Fetch fresh market data"""
        self.logger.info(f"Fetching market data for {len(TICKERS)} tickers...")
        self.current_data = self.fetcher.fetch_all(TICKERS)
        self.last_data_refresh = datetime.now()
        self.logger.info(f"Successfully fetched data at {self.last_data_refresh}")

    def check_rules(self):
        """Evaluate all rules against current data"""
        if not self.current_data:
            self.logger.warning("No data available. Skipping rule check.")
            return

        self.logger.info("Checking rules against market data...")
        evaluations = self.engine.evaluate_all(self.current_data)
        self.last_rule_check = datetime.now()

        # Display evaluations
        print_evaluations(evaluations)

        # Process signals and trigger alerts
        for eval in evaluations:
            self.process_signal(eval)

        self.logger.info(f"Rule check completed at {self.last_rule_check}")

    def process_signal(self, evaluation):
        """Process a rule evaluation and trigger actions"""
        ticker = evaluation.ticker
        signal = evaluation.signal
        reason = evaluation.reason

        if signal == Signal.BUY:
            self.handle_buy_signal(ticker, reason, evaluation)
        elif signal == Signal.SELL:
            self.handle_sell_signal(ticker, reason, evaluation)
        elif signal == Signal.REDUCE:
            self.handle_reduce_signal(ticker, reason, evaluation)

    def handle_buy_signal(self, ticker, reason, evaluation):
        """Handle buy signal"""
        if ticker not in self.positions or not self.positions[ticker]:
            alert_msg = f"🔔 BUY SIGNAL: {ticker}\n{reason}"
            self.logger.info(alert_msg)
            self.send_alert(alert_msg)
            self.positions[ticker] = True
        else:
            self.logger.debug(f"Already holding {ticker}, skipping buy signal")

    def handle_sell_signal(self, ticker, reason, evaluation):
        """Handle sell signal"""
        if ticker in self.positions and self.positions[ticker]:
            alert_msg = f"🔔 SELL SIGNAL: {ticker}\n{reason}"
            self.logger.info(alert_msg)
            self.send_alert(alert_msg)
            self.positions[ticker] = False
        else:
            self.logger.debug(f"Not holding {ticker}, skipping sell signal")

    def handle_reduce_signal(self, ticker, reason, evaluation):
        """Handle reduce position signal"""
        alert_msg = f"⚠️  REDUCE POSITION: {ticker}\n{reason}"
        self.logger.warning(alert_msg)
        self.send_alert(alert_msg)

    def send_alert(self, message):
        """Send alert through configured channels"""
        if not ALERTS_ENABLED:
            return

        # TODO: Implement actual alert channels (email, Slack, Discord, etc.)
        # For now, just log to console and file
        print(f"\n{'*' * 80}")
        print(f"ALERT: {message}")
        print(f"{'*' * 80}\n")

    def run_once(self):
        """Run one iteration of the monitor"""
        self.logger.info("=" * 80)
        self.logger.info(f"Market Monitor Agent cycle - {datetime.now()}")
        self.logger.info("=" * 80)

        # Fetch data
        self.fetch_market_data()

        # Check rules
        self.check_rules()

        self.logger.info("Cycle complete\n")

    def run(self, interval_seconds=60, max_iterations=None):
        """
        Run the agent in a loop

        Args:
            interval_seconds (int): How often to run a cycle
            max_iterations (int): Stop after N iterations (for testing). None = infinite.
        """
        self.logger.info("🚀 Market Monitor Agent starting...")
        self.logger.info(f"Monitoring tickers: {TICKERS}")

        iteration = 0
        try:
            while True:
                self.run_once()

                iteration += 1
                if max_iterations and iteration >= max_iterations:
                    self.logger.info(f"Reached max iterations ({max_iterations}). Stopping.")
                    break

                self.logger.info(f"Next cycle in {interval_seconds} seconds...\n")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("\n⏸️  Agent interrupted by user. Shutting down.")
        except Exception as e:
            self.logger.error(f"Fatal error in agent loop: {e}", exc_info=True)
            raise


def main():
    """Entry point"""
    # For demo purposes, run a single iteration with quick checks
    agent = MarketMonitorAgent()

    # Run one cycle for testing
    agent.run_once()

    # Uncomment below to run continuously:
    # agent.run(interval_seconds=300)  # Check every 5 minutes


if __name__ == "__main__":
    main()
