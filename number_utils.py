def transNumber(s:str) -> int:
    unit_map = {"만": 10_000, "천": 1_000, "억": 100_000_000}
    s = s.strip().replace(",", "")  # 공백·콤마 제거

    for unit, mul in unit_map.items():
        if s.endswith(unit):
            try:
                num = float(s[:-1])
            except ValueError:
                return 0
            return int(num * mul)

    # 단위 없으면 그대로 정수 변환
    try:
        return int(s)
    except ValueError:
        return 0