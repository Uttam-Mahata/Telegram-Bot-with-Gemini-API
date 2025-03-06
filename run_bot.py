#!/usr/bin/env python3
"""
Script to run the Learning Bot.
"""
import asyncio
import logging
from learning_bot import main

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
        import sys
        sys.exit(1)