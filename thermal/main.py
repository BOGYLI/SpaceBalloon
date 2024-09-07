"""
Read data from thermal cam sensor

CSV format:
timestamp, 0, 1, 2, ..., 767
"""

import utils
import board
import busio
import adafruit_mlx90640


# Initialize logger
logger = utils.init_logger("thermal")


def get_frame(mlx):
    frame = [0] * 768
    try:
        mlx.getFrame(frame)
    except ValueError:
        # these happen, no biggie - retry
        return get_frame(mlx)
    return frame


def main():

    i2c = busio.I2C(board.SCL, board.SDA)

    mlx = adafruit_mlx90640.MLX90640(i2c)

    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

    while True:

        frame = get_frame(mlx)

        min_temp = min(frame)
        max_temp = max(frame)
        avg_temp = sum(frame) / len(frame)
        median_temp = sorted(frame)[len(frame) // 2]

        logger.info(f"Min: {min_temp:.3f}°C, Max: {max_temp:.3f}°C, Avg: {avg_temp:.3f}°C, Median: {median_temp:.3f}°C")
        utils.write_csv("thermal", [min_temp, max_temp, avg_temp, median_temp, *[f"{temp:.3f}" for temp in frame]])
        utils.send_data("thermal", {"pixels": frame}, logger)


if __name__ == "__main__":

    main()
