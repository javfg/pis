import unittest
from definitions import ROOT_DIR
import subprocess
import os

from modules.helpers.HPO import HPO
from modules.helpers.EFO import EFO
from modules.helpers.HPOPhenotypes import HPOPhenotypes
from modules.helpers.MONDO import MONDO

class TestDiseaseStep(unittest.TestCase):
    """
    TBC: To be complete
    """

    def setUp(self):
        self.hpo_filename = ROOT_DIR+"/tests/resources/hp.jsonl"
        self.efo_filename = ROOT_DIR+"/tests/resources/efo.jsonl"
        self.phenotype_filename = ROOT_DIR+"/tests/resources/phenotype.hpoa"
        self.mondo_filename = ROOT_DIR + "/tests/resources/mondo.jsonl"


    def testDisease(self):
        EFOModule = EFO(self.efo_filename)
        process = subprocess.Popen("cat "+ self.efo_filename +"| grep -v deprecated | grep -v 'Restric' | grep -v 'intersectionOf' | wc -l",
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   )
        num_valid_EFO = int(process.communicate()[0].decode("utf-8").replace("\n",""))
        EFOModule.generate()
        assert len(EFOModule.diseases) == num_valid_EFO

    # exclude obsolete term
    def testHPO(self):
        HPOModule = HPO(self.hpo_filename)
        process = subprocess.Popen("cat "+ self.hpo_filename +"| grep -v deprecated | wc -l",
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   )
        num_valid_HPO = int(process.communicate()[0].decode("utf-8").replace("\n", ""))
        HPOModule.generate()
        assert len(HPOModule.hpo) == num_valid_HPO

    #def testHPOPhenotypes(self):
    #    HPModule = HPOPhenotypes(self.phenotype_filename)
    #    outfile = HPModule.run('test_phenotype.jsonl')
    #    assert (os.stat(outfile).st_size > 0) == True

    def testMONDO(self):
        MondoModule = MONDO(self.mondo_filename)
        process = subprocess.Popen("cat "+ self.mondo_filename +"| grep -v deprecated | wc -l",
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   )
        num_valid_MONDO = int(process.communicate()[0].decode("utf-8").replace("\n", ""))
        MondoModule.generate()
        assert len(MondoModule.mondo) == num_valid_MONDO

