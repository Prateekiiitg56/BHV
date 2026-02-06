"""Entry point to run the BHV minimalist monolith.

Usage: python run.py

It picks up `MONGO_URI` environment variable to use MongoDB; otherwise uses TinyDB.
"""
import os
from bhv.full_app import create_app


def main():
    port = int(os.environ.get('PORT', 5000))
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()
