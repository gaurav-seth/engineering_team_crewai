from app import build_demo


def main() -> None:
    demo = build_demo()
    assert demo is not None
    print("Blocks constructed successfully")


if __name__ == "__main__":
    main()
