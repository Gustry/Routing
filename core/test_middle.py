import unittest

from middle import get_distance, get_distances, get_middle, split_middle
from math import sqrt


class TestMiddle(unittest.TestCase):

    def setUp(self):
        self.p1 = (0, 0)
        self.p2 = (4, 0)
        self.p3 = (4, 4)
        self.p4 = (0, 4)
        self.p5 = (1, 1)
        self.l1 = (self.p1, self.p2, self.p3, self.p4)
        self.l2 = [(0, 0), (1, 1), (3, 3), (4, 4)]
        self.l3 = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]

    def tearDown(self):
        pass

    def test_get_distance(self):
        self.assertEqual(get_distance(self.p1, self.p2), 4)
        self.assertEqual(get_distance(self.p2, self.p3), 4)
        self.assertEqual(get_distance(self.p4, self.p3), 4)
        self.assertEqual(get_distance(self.p5, self.p1), sqrt(2))
        self.assertEqual(get_distance(self.p3, self.p5), sqrt(18))

    def test_get_distances(self):
        self.assertEquals(sum(get_distances(self.l1)), 12)

    def test_get_middle(self):
        self.assertEquals(get_middle(self.p1, self.p2), (2, 0))
        self.assertEquals(get_middle(self.p1, self.p5), (0.5, 0.5))
        self.assertEquals(get_middle(self.p5, self.p3), (2.5, 2.5))

    def test_split_middle(self):
        r = ([(0, 0), (4, 0), (4, 4)], [(4, 4), (0, 4), (0, 0)])
        self.assertEquals(split_middle(self.l3), r)

        r = ([(0, 0), (1, 1), (2, 2)], [(2, 2), (3, 3), (4, 4)])
        self.assertEquals(split_middle(self.l2), r)

        l = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        r = ([(0, 0), (1, 1), (2, 2), (2.5, 2.5)], [(2.5, 2.5), (3, 3), (4, 4), (5, 5)])
        self.assertEquals(split_middle(l), r)

        l = [(0, 0), (2, 2), (3, 3), (4, 4), (5, 5)]
        r = ([(0, 0), (2, 2), (2.5, 2.5)], [(2.5, 2.5), (3, 3), (4, 4), (5, 5)])
        self.assertEquals(split_middle(l), r)

        l = [(0, 0), (4, 0)]
        r = ([(0, 0), (2, 0)], [(2, 0), (4, 0)])
        self.assertEquals(split_middle(l), r)

if __name__ == '__main__':
    unittest.main()
