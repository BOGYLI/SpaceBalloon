"""
APRS ground station receiving packets
"""

import uvicorn
import os


def main():

    os.environ["PYTHONUNBUFFERED"] = "1"

    uvicorn.run("app:app", host="0.0.0.0", port=8080, app_dir=os.getcwd())


if __name__ == "__main__":

    main()
