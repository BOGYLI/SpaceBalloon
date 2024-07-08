"""
Collect all sensor data via a HTTP server and transmit it
"""

import uvicorn
import os


def main():

    uvicorn.run("app:app", host="0.0.0.0", port=8000, app_dir=os.getcwd())


if __name__ == "__main__":

    main()
