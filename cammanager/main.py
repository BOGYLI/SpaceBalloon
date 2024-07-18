"""
Communicate with cameras and mission control
"""

import uvicorn
import os


def main():

    uvicorn.run("app:app", host="0.0.0.0", port=80, app_dir=os.getcwd())


if __name__ == "__main__":

    main()
