# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10, 2019

@author: Parthan S Olikkal
@UMBC ID: SH25379
"""

from MultiPipelineAnalyzer import MultiPipelineAnalyzer
import sys

if __name__ == "__main__":
    try:
        arch = MultiPipelineAnalyzer(sys.argv[4], sys.argv[1], sys.argv[3], "./instructionSet.txt", sys.argv[2])
        arch.simulateInstructions()
        arch.printOutputTable()
        arch.writeOutputFile(sys.argv[5])
    
    except Exception as exc:
        pass
