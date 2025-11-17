import random

class GachaBanner:
    def __init__(self, unit_cls, lvlVec_len):
        self.unit_cls = unit_cls
        self.lvlVec_len = lvlVec_len

    def base_unit(self):
        return self.unit_cls()

    def draw_unit(self):
        level = self._draw_level()
        lvlVec = self._random_partition(level, self.lvlVec_len)
        grade = self._grade_from_level(level)
        unit = self.unit_cls(lvlVec=lvlVec, level=level, letterrank=grade)
        return unit

    def _draw_level(self):
        """Geometric distribution with P(0)=0.1, P(n)=0.9*P(n-1)."""
        level = 0
        while random.random() < 0.9:
            level += 1
        return level

    def _random_partition(self, total, length):
        """Distribute 'total' levels randomly across 'length' stats, 
        each level choosing a stat independently."""
        parts = [0] * length
        for _ in range(total):
            idx = random.randrange(length)
            parts[idx] += 1
        return parts

    def _grade_from_level(self, level):
        """Map numeric level to grade string with +/- tags."""
        grades = ["F-","F","F+","E-","E","E+","D-","D","D+","C-","C","C+","B-","B","B+","A-","A","A+","S-","S","S+","SS-","SS","SS+","SSS-","SSS","SSS+","U-","U","U+"]
        if level < len(grades):
            base = grades[level]
        else:
            # Extend infinitely: after U, use L-prefixed sequence
            n = level - len(grades)
            base = "L"*(n//30 + 1) + grades[n % len(grades)]

        return base
