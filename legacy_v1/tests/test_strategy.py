import unittest
from ai_trade_check.strategy import signal,levels,quantity
class T(unittest.TestCase):
 def test_long(self):
  self.assertEqual(signal([1,100,120,95,115,1],[0,100,110,90,105,1]).side,"long")
 def test_short(self):
  self.assertEqual(signal([1,100,105,80,85,1],[0,100,110,90,105,1]).side,"short")
 def test_levels(self):
  self.assertEqual(levels("long",100,95,2)["target"],110)
if __name__=="__main__": unittest.main()
