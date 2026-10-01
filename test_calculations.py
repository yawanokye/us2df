import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from calculations import *

class CalculationTests(unittest.TestCase):
    def test_ceiling(self):
        self.assertEqual(count(384.15),385)
        self.assertEqual(count(266.77),267)
        self.assertEqual(count(663.49),664)
        self.assertEqual(count(460.76),461)
        self.assertEqual(count(385.0),385)
        self.assertEqual(count(0),0)
    def test_precision(self):
        self.assertEqual(precision(50000,2,.05,.95),382)
        self.assertEqual(precision(50000,4,.03,.95),266)
        self.assertEqual(precision(200,2,.05,.95),132)
    def test_limits(self):
        self.assertEqual([precision_limit(r,e,c) for r,e,c in [(2,.05,.95),(4,.03,.95),(2,.05,.99),(4,.03,.99)]],[385,267,664,461])
    def test_exact_t(self):
        self.assertEqual([mean_requirement(d)["per_group"] for d in [.2,.5,.8]],[394,64,26])
    def test_minimum_power(self):
        for d in [.2,.5,.8]:
            n=mean_requirement(d)["per_group"]
            self.assertGreaterEqual(mean_power(n,d),.8-1e-12)
            self.assertLess(mean_power(n-1,d),.8)
    def test_reference_values(self):
        self.assertEqual([REFERENCES[k][1] for k in ["Small","Medium","Large"]],[400,65,30])
    def test_one_sample(self):
        result=mean_requirement(.5,groups=1)
        self.assertEqual(result["total"],result["per_group"])
        self.assertGreaterEqual(mean_power(result["total"],.5,groups=1),.8)
    def test_two_proportions(self):
        result=two_proportions(.5,.6)
        self.assertEqual(result["total"],2*result["per_group"])
        self.assertIsInstance(result["per_group"],int)
    def test_zero_effect(self):
        for fn in [lambda:two_proportions(.5,.5),lambda:one_proportion(.5,.5),lambda:mean_requirement(0)]:
            with self.assertRaises(ValueError): fn()
    def test_one_proportion(self):
        self.assertEqual(one_proportion(.5,.6)["total"],one_proportion(.5,.6)["per_group"])
    def test_anova(self):
        result=anova_requirement(.25,3)
        self.assertEqual(result["total"],3*result["per_group"])
        self.assertGreater(result["total"],0)
    def test_green(self):
        self.assertEqual(green(10),130)
        self.assertEqual(green(10,False,True),114)
    def test_logistic(self):
        self.assertEqual(logistic(10,.1,10),1000)
        self.assertEqual(logistic(10,.9,10),1000)
    def test_sem(self):
        self.assertEqual(sem_screen(3,4,10),(270,27))
    def test_reconcile(self):
        result=reconcile({"Precision":385,"Power":130},50000,1.5,1.2,.2)
        self.assertEqual(result["base"],385)
        self.assertEqual(result["uncapped"],867)
        self.assertEqual(result["binding"],["Precision"])
    def test_cap(self):
        result=reconcile({"Power":800},500)
        self.assertEqual(result["uncapped"],800)
        self.assertEqual(result["operational"],500)
        self.assertTrue(result["exceeds_population"])
    def test_no_components(self):
        with self.assertRaises(ValueError):reconcile({},500)
    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):count(float("nan"))
        with self.assertRaises(ValueError):reconcile({"Power":100},500,nonresponse=1)
        with self.assertRaises(ValueError):green(10,False,False)
    def test_syntax(self):
        import ast
        ast.parse((Path(__file__).resolve().parents[1]/"app.py").read_text())

if __name__=="__main__":
    unittest.main()
