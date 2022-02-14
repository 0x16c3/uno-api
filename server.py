import argparse, uvicorn
import utils.config

import main


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process some integers.")

    parser.add_argument(
        "--debug",
        dest="debug",
        type=str2bool,
        nargs="?",
        default=False,
        const=True,
        help="enable debug mode",
    )

    parser.add_argument(
        "--info",
        dest="info",
        type=str2bool,
        nargs="?",
        default=False,
        const=True,
        help="enable info mode",
    )

    args = parser.parse_args()

    log_level = "error"
    reload = False

    if args.info:
        log_level = "info"
    if args.debug:
        log_level = "debug"
        reload = True

    uvicorn.run(
        "main:app",
        host=utils.config["APP_HOST"],
        port=int(utils.config["APP_PORT"]),
        log_level=log_level,
        reload=reload,
        # The following is needed to make nginx pass the correct headers
        proxy_headers=True,
    )
