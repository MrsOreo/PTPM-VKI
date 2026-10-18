class Converter:
    @staticmethod
    def do(x: float) -> int:
        if x == 0.0:
            raise ValueError("Значение не может быть равно нулю.")
        if x >= 100.7:
            return 1000
        if x <= -30.5:
            return -2000
        if x > 0:
            return int(x)
        return int(x) - 5
