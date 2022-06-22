import math

class Point4D:
    def __init__(self, x=0, y=0, z=0, c=0):
        self.x = x
        self.y = y
        self.z = z
        self.c = c

    def fromDict(self, dictDesc):
        for key, val in dictDesc.values():
            if key.upper() == 'X':
                self.x = val
            elif key.upper() == 'Y':
                self.y = val
            elif key.upper() == 'Z':
                self.z = val
            elif key.upper() == 'C':
                self.c = val
        return self

    def toDict(self):
        """
        Return a dict like {'X':valx, 'Y':valz, 'Z':valz, 'C'=valt}
        :return:
        """
        return {'X': self.x, 'Y': self.y, 'Z': self.z, 'C': self.c}



def normalizeAngle(angle):
    """
    :param angle:in degrees (float)
    :return: (float) Angle in degrees in [-180, 180]
    """
    angle = math.radians(angle)

    while angle > math.pi:
        angle -= 2.0 * math.pi

    while angle < -math.pi:
        angle += 2.0 * math.pi

    return math.degrees(angle)


print(normalizeAngle(359))
