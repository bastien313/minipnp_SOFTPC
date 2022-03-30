import math


class Corrector:
    def __init__(self):
        self.posx = 0.0  # is the CAD posX in file.
        self.posy = 0.0  # is the CAD posX in file.
        self.posref = [0, 0, 0, 0]  # contain position of mesured ref, used only for save
        self.xOffset = 0.0  # is the calculated offsetX
        self.yOffset = 0.0  # is the calculated offsetY
        self.angleCorr = 0.0  # is the calculated angle

    def pointCorrection(self, posIn):
        """
        Compute correction of component pos.
        :param posIn: is position of point [X,Y]:
        :return a lsit of position correcter [Xcorr,Ycorr]:
        """

        x = posIn[0]
        y = posIn[1]
        angle = math.radians(self.angleCorr)

        # on ramene le composant au zero(pos)
        x -= self.posx
        y -= self.posy

        hypotenuse = math.hypot(x, y)
        # on calcule l'angle actuel
        actualAngle = math.atan2(y, x)

        # on applique la rotation.
        x = math.cos(angle + actualAngle) * hypotenuse
        y = math.sin(angle + actualAngle) * hypotenuse

        # on reposition apres rotation.
        x += self.posx
        y += self.posy

        # On applique l'offset
        x += self.xOffset
        y += self.yOffset

        return [x, y]

    def buildCorrector(self, ref1, ref2, pos1, pos2):
        """
        Compute xOffset, yOffset and angleCorr.
        ref1 etc is [X,Y]
        ref is the mesured value, pos is the CAD position
        :return:
        """
        self.posref[0] = ref1[0]
        self.posref[1] = ref1[1]
        self.posref[2] = ref2[0]
        self.posref[3] = ref2[1]

        r2 = [0, 0]
        p1 = [0, 0]
        p2 = [0, 0]

        r2[0] = ref2[0] - ref1[0]
        p1[0] = pos1[0] - ref1[0]
        p2[0] = pos2[0] - ref1[0]

        r2[1] = ref2[1] - ref1[1]
        p1[1] = pos1[1] - ref1[1]
        p2[1] = pos2[1] - ref1[1]

        L = r2[0]
        H = r2[1]
        Q = math.atan2(H, L)

        Lp = p2[0] - p1[0]
        Hp = p2[1] - p1[1]
        Qp = math.atan2(Hp, Lp)

        self.posx = pos1[0]
        self.posy = pos1[1]

        self.angleCorr = Q - Qp
        self.angleCorr = math.degrees(self.angleCorr)
        self.xOffset = p1[0]*-1.0
        self.yOffset = p1[1]*-1.0
