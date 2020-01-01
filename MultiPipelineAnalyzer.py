# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10, 2019

@author: Parthan S Olikkal
@UMBC ID: SH25379
"""

import io
import queue
import re
from copy import deepcopy
from heapq import heappush, heapreplace

class MultiPipelineAnalyzer(object):
    
    #Constructor
    def __init__(self, configFilePath, instrFilePath, registerFilePath, instructionSetFilePath, memoryFilePath):
        self.outputTable = {}
        self.pipelineConfiguration = self.readConfigFile(configFilePath)
        self.instructionSet = self.readInstructionSet(instructionSetFilePath)
        self.prepareArchitecture(registerFilePath, memoryFilePath)
        self.instructions, self.labels = self.readInstructionsFile(instrFilePath) 
                
    #Reads the configuration file that is given as argument in commandline    
    def readConfigFile(self, filePath):
        configFile = io.open(filePath)
        cfg = {}
        
        fileLine = configFile.readline()
        while fileLine:
            cfg[fileLine.split(":")[0].lower().strip()] = fileLine.split(":")[1].strip().split(",")
            fileLine = configFile.readline()
        
        #Error status for invalid configurations
        errorStatus = [False]
        msg = ""
        for key, val in cfg.items():
            patternMatch = re.search("^fp", key)
            if patternMatch:
                if val == None or len(val) <= 1 or val[0] == '':
                    errorStatus = [True]
                    msg += "Error in Config Element: " + key + "\nPlease enter a valid config\n\n"
                elif int(val[0]) < 0:
                    errorStatus = [True]
                    msg += "Error in Config Element: " + key + "\nPlease enter a valid number of cycles\n\n"   
            else:
                if val == None or len(val) == 0 or val[0] == '':
                    errorStatus = [True]
                    msg += "Error in Config Element: " + key + "\nPlease enter a valid config\n\n"
                elif int(val[0]) < 0:
                    errorStatus = [True]
                    msg += "Error in Config Element: " + key + "\nPlease eneter a valid number of cycles\n\n"
        if errorStatus[0]:
            print("Errors in configuration file\n Please enter a valid configuration file\n\n" + msg)
            raise Exception("Errors in configuration file\n Please enter a valid configuration file" + msg)
        return cfg
    
    #Reads all the different types of instructions mentioned
    def readInstructionSet(self, instructionSetFilePath):
        if True:
            instructionSet = {"hlt":"NO_EX",
                              "j":"NO_EX",
                              "beq":"NO_EX",
                              "bne":"NO_EX",
                              "dadd":"INT",
                              "daddi":"INT",
                              "dsub":"INT",
                              "dsubi":"INT",
                              "and":"INT",
                              "andi":"INT",
                              "or":"INT",
                              "ori":"INT",
                              "lw":"MEM",
                              "sw":"MEM",
                              "l.d":"MEM",
                              "s.d":"MEM",
                              "add.d":"FP_ADD",
                              "sub.d":"FP_ADD",
                              "mul.d":"FP_MUL",
                              "div.d":"FP_DIV"}
        else:
            instructionSet = {}
            instructionSetFile = io.open(instructionSetFilePath)
            fileLine = instructionSetFile.readline().strip()
            while fileLine:
                instructionSet[fileLine.strip().split(',')[0].strip().lower()] = fileLine.strip().split(',')[1].strip()
                fileLine = instructionSetFile.readline().strip()
        
        return instructionSet
    
    #Reads the instruction file from the command line which is given    
    def readInstructionsFile(self, filePath):
        instrFile = io.open(filePath)
        instructions = {}
        labels = {}
        
        instructionIndex = 1
        
        instruction = instrFile.readline().strip().lower()
        while instruction:
            # extract label for instruction if any and record the reference in the label index
            if len(instruction.split(":")) > 1:
                label = instruction.split(":")[0].strip()
                labels[label] = str(instructionIndex)
                # strip label from instruction
                instruction = instruction.split(":")[1].strip()
            
            tokens = instruction.split(' ', 1)
            opcode = tokens[0].strip()
            if len(tokens) == 1:
                # no operands present
                operands = ""
           
            elif opcode in ["j", "bne", "beq"]:
                operands = []
                operandTokens = tokens[1].strip().split(',')
                
                for token in operandTokens:
                    operands.append(token.strip())
           
            else:  
                # process operands present to extract register operands
                operands = []
                operandTokens = tokens[1].strip().split(',')
                
                for token in operandTokens:
                    operand = token.strip()
                    patternMatch = re.search("[r,f]\d+", operand)
                    if patternMatch:
                        operands.append(patternMatch.group(0).strip("("))
                    patternMatch = re.search("^\d*\(", operand)
                    if patternMatch:
                        operands.append(patternMatch.group(0).strip("("))
                    patternMatch = re.search("^\d*$", operand)
                    if patternMatch:
                        operands.append(patternMatch.group(0).strip("("))
                    
                
            instructions[str(instructionIndex)] = {"opcode": opcode, "operands": operands}
            instructionIndex += 1
            instruction = instrFile.readline().strip().lower()        
        return instructions, labels

    #Reads the memory file and the register file
    def prepareArchitecture(self, registerFilePath, memoryFilePath):
        self.clock = 0
        self.executionComplete = False
        self.halt = False
        
        self.multipathPipeline = {
                                  "MST_SEQ":["IF", "ID", "INT_EX", "MEM", "FP_ADD", "FP_DIV", "FP_MUL", "WB"],
                                  "INT_SEQ":["INT_EX", "MEM"],
                                  "CYCLE_TIMES":{
                                                 "IF": int(self.pipelineConfiguration["i-cache"][0].strip()),
                                                 "ID": 1,
                                                 "INT_EX":1,
                                                 "MEM":int(self.pipelineConfiguration["main memory"][0].strip()),
                                                 "FP_ADD":int(self.pipelineConfiguration["fp adder"][0].strip()),
                                                 "FP_MUL":int(self.pipelineConfiguration["fp multiplier"][0].strip()),
                                                 "FP_DIV":int(self.pipelineConfiguration["fp divider"][0].strip()),
                                                 "WB":1
                                                 },
                                  "IF":queue.Queue(maxsize=1),
                                  "ID":queue.Queue(maxsize=1),
                                  "INT_EX":queue.Queue(maxsize=1),
                                  "MEM":queue.Queue(maxsize=1),
                                  "FP_ADD":queue.Queue(maxsize=1),
                                  "FP_MUL":queue.Queue(maxsize=1),
                                  "FP_DIV":queue.Queue(maxsize=1),
                                  "WB":queue.Queue(maxsize=1)
                                  }
        
        if self.pipelineConfiguration["fp adder"][1].strip() == "yes":
            self.multipathPipeline["FP_ADD"].maxsize = int(self.pipelineConfiguration["fp adder"][0].strip())  
            
        if self.pipelineConfiguration["fp multiplier"][1].strip() == "yes":
            self.multipathPipeline["FP_MUL"].maxsize = int(self.pipelineConfiguration["fp multiplier"][0].strip())  
            
        if self.pipelineConfiguration["fp divider"][1].strip() == "yes":
            self.multipathPipeline["FP_DIV"].maxsize = int(self.pipelineConfiguration["fp divider"][0].strip())  
        
        self.initializeRegisterStatusVector()
        self.initializeRegisterFile(registerFilePath)
        self.initializeMemory(memoryFilePath)
        self.instructionCache = [[], [], [], []]
        self.dataCache = [[], []]
        self.instructionCacheHit = 0
        self.instructionCacheMiss = 0
        self.dataCacheHit = 0
        self.dataCacheMiss = 0
        self.branchTaken = False
        self.dataBusInUse = [False]
    
    #initializes register file with the given register file  
    def initializeRegisterFile(self, registerFilePath):
        registerFile = io.open(registerFilePath)
        registerIndex = 0
        self.registerFile = {}
        registerValue = registerFile.readline()
        while registerValue:
            self.registerFile["r" + str(registerIndex)] = int(registerValue, 2)
            registerValue = registerFile.readline()
            registerIndex += 1
    
    #initialzes memory with the given memory file            
    def initializeMemory(self, memoryFilePath):
        memoryFile = io.open(memoryFilePath)
        memoryWordIndex = 0
        self.dataMemory = {}
        memoryWord = memoryFile.readline()
        while memoryWord:
            self.dataMemory[str(memoryWordIndex)] = int(memoryWord, 2)
            memoryWord = memoryFile.readline()
            memoryWordIndex += 1
    
    #Initializes register read/write status vector      
    def initializeRegisterStatusVector(self):
        self.register_status = {}
        for index in range(1, 33):
            self.register_status["r" + str(index)] = {"R":0, "W":0}
            self.register_status["f" + str(index)] = {"R":0, "W":0}
   
    #Stimulates the instruction from instruction file, loading instruction through pipeline    
    def simulateInstructions(self):
        self.programCounter = 1
        outputIndex = 1
        while self.programCounter <= len(self.instructions) :
            if self.programCounter == 1:
                # loading first instruction in pipeline
                self.fetchInstruction(self.programCounter, outputIndex)
                self.multipathPipeline["IF"].put(
                                                 [
                                                  [outputIndex, self.programCounter],
                                                  self.instructions[str(self.programCounter)]["opcode"],
                                                  2 * (int(self.pipelineConfiguration["i-cache"][0]) + int(self.pipelineConfiguration["main memory"][0])),
                                                  [],
                                                  ["miss", 1]
                                                  ]
                                                 )
                self.outputTable[outputIndex] = {
                                                 "INSTR": self.programCounter,
                                                 "IF":0,
                                                 "ID":0,
                                                 "EX":0,
                                                 "WB":0,
                                                 "RAW":False,
                                                 "WAR":False,
                                                 "WAW":False,
                                                 "STRUCT":False
                                                 }
                self.programCounter += 1 
                outputIndex += 1 
                
            else:  
                # progress existing pipeline state before attempting to fetch next instruction 
                self.progressPipeline()
                if self.multipathPipeline["IF"].empty():
                    self.multipathPipeline["IF"].put(self.fetchInstruction(self.programCounter, outputIndex))
                    self.outputTable[outputIndex] = {
                                                     "INSTR": self.programCounter,
                                                     "IF":0,
                                                     "ID":0,
                                                     "EX":0,
                                                     "WB":0,
                                                     "RAW":False,
                                                     "WAR":False,
                                                     "WAW":False,
                                                     "STRUCT":False
                                                     }
                    self.programCounter += 1 
                    outputIndex += 1 
            
            # ready for next clock cycle
            self.clock += 1
            
        
        # wait for execution completion after loading all instructions in pipeline
        while not self.executionComplete:
            self.progressPipeline()
            self.clock += 1
            
        # initialize execution completion cycle value
        self.executionCompleteCycle = 0
        # execution completes in cycle when last instruction completes
        for key, value in list(self.outputTable[len(self.outputTable)].items()):
            if key in ["ID", "WB"]:
                # instruction can complete execution only in ID or WB
                self.executionCompleteCycle = value if self.executionCompleteCycle < value else self.executionCompleteCycle
    
    #Method should be called when the instruction is issue
    #(at instruction decode stage) to set the status of registers used as operands
    def setRegisterStatus(self, instruction):
        operands = self.instructions[instruction]["operands"]
        opcode = self.instructions[instruction]["opcode"].strip()
        if operands != "":
            if opcode not in ["SW", "S.D"] and self.instructionSet[opcode] != "NO_EX":
                self.register_status[operands[0].strip()]["W"] += 1
     
    #This method should be called upon all but first clock cycle. It propagates instructions through pipeline stages                
    def progressPipeline(self):
        emptyStageCount = 0
        
        nextStage = "END"
        pipelineStages = deepcopy(self.multipathPipeline["MST_SEQ"])
        pipelineStages.reverse()
        for currentStage in pipelineStages:
            if not self.multipathPipeline[currentStage].empty():
                # check id current stage is IF and branch taken flag is set
                if currentStage == "IF" and self.branchTaken:
                    instructionState = self.multipathPipeline[currentStage].get()
                    if instructionState[1].strip() not in ["sw", "s.d"] and self.instructionSet[instructionState[1]] != "NO_EX":
                        self.register_status[self.instructions[str(instructionState[0][1])]["operands"][0].strip()]["W"] -= 1
                    self.updateOutputTableStageCompletion(instructionState[0][0], currentStage)
                    self.branchTaken = False
                    continue
                # create temp queue
                updatedStageQueue = queue.Queue(maxsize=self.multipathPipeline[currentStage].maxsize)
                while not self.multipathPipeline[currentStage].empty():
                    instructionState = self.multipathPipeline[currentStage].get()
                    if instructionState[2] > 0:
                        # # instruction hasn't completed current stage and persist in this stage for this cycle
                        
                        # check if instruction in IF / MEM stage and is going through cache miss
                        if currentStage in ["IF", "MEM"] and instructionState[4][0] != "hit":
                            # if data bus in use
                            if self.dataBusInUse[0]:
                                # if current instruction using data bus proceed
                                if self.dataBusInUse[1] == instructionState[0][0]:
                                    instructionState[2] -= 1
                                    updatedStageQueue.put(instructionState)
                                    if currentStage == "IF" and instructionState[2] == 0:
                                        self.dataBusInUse = [False]
                                else:
                                    # stall
                                    if instructionState[4][1] == self.clock - 1 and currentStage == "MEM":
                                        instructionState[2] += 1
                                    updatedStageQueue.put(instructionState)
                            else:
                                self.dataBusInUse = [True, instructionState[0][0], instructionState[4][1]]
                                instructionState[2] -= 1
                                updatedStageQueue.put(instructionState)
                        else:  # normally proceed
                            instructionState[2] -= 1
                            updatedStageQueue.put(instructionState)
                    else: 
                        # handle data bus contention flag
                        if self.dataBusInUse[0]:
                            if self.dataBusInUse[1] == instructionState[0][0]:
                                self.dataBusInUse = [False]
                                
                        # instruction has completed this stage
                        
                        nextStage = self.getNextStage(instructionState, currentStage)
                        if nextStage != "END":
                            
                            # check for any instruction hazards
                            hazards = self.checkHazards(instructionState[0][1], currentStage, nextStage)
                            if len(hazards) == 0:
                                if currentStage != "MEM":
                                    # execute current stage actions for instruction
                                    instructionState = self.executeStageActions(instructionState, currentStage)
                                
                                # write cycle time for instruction current stage completion to file
                                self.updateOutputTableStageCompletion(instructionState[0][0], currentStage)
                                
                                if currentStage == "IF" and instructionState[1] == "hlt" and self.halt:
                                    return
                            
                                # enqueue instruction on next stage
                                self.enqueueInNextStage(instructionState, currentStage, nextStage)
                            else:
                                # hazards detected...log hazard in output table
                                self.updateOutputTableHazard(instructionState[0][0], hazards)
                                # stall instruction in current phase
                                updatedStageQueue.put(instructionState)
                        else:
                            hazards = self.checkHazards(instructionState[0][1], currentStage, nextStage)
                            if len(hazards) == 0:
                                # instruction complete. reset write register status vector for destination register
                                instructionState = self.executeStageActions(instructionState, currentStage)
                                if instructionState[1].strip() not in ["sw", "s.d"] and self.instructionSet[instructionState[1]] != "NO_EX":
                                    self.register_status[self.instructions[str(instructionState[0][1])]["operands"][0].strip()]["W"] -= 1
                                self.updateOutputTableStageCompletion(instructionState[0][0], currentStage)
                                if instructionState[1] == "hlt":
                                    self.halt = True
                            else:
                                # hazards detected, log hazard in output table
                                self.updateOutputTableHazard(instructionState[0][0], hazards)
                                # stall instruction in current phase
                                updatedStageQueue.put(instructionState)
                self.multipathPipeline[currentStage] = updatedStageQueue
            else:
                # no instruction in current stage, process next stage
                emptyStageCount += 1
                continue
            
        if emptyStageCount == len(self.multipathPipeline["MST_SEQ"]):
            self.executionComplete = True
    
    #Method should be called to retrieve the next stage for the instruction
    def getNextStage(self, instructionState, currentStage):
        nextStage = ""
        
        if currentStage == "ID":
            # check if instruction is branch
            if self.instructionSet[instructionState[1]] == "NO_EX":
                nextStage = "END"
            # else choose execution path 
            elif self.instructionSet[instructionState[1]] in ["INT", "MEM"]:
                nextStage = "INT_EX"
            elif self.instructionSet[instructionState[1]] == "FP_ADD":
                nextStage = "FP_ADD"
            elif self.instructionSet[instructionState[1]] == "FP_DIV":
                nextStage = "FP_DIV"
            elif self.instructionSet[instructionState[1]] == "FP_MUL":
                nextStage = "FP_MUL"
        elif currentStage == "INT_EX":
            # if current stage in integer execution then next stage is memory
            nextStage = "MEM"
        elif currentStage in ["MEM", "FP_ADD", "FP_DIV", "FP_MUL"]:
            # if current stage is execution then next stage is write back
            nextStage = "WB"
        elif currentStage == "WB":
            nextStage = "END"
        else:
            nextStage = "ID"
            
        return nextStage  
    
    #Method checks for instruction hazards. It should be called when the 
    #instruction completes current stage and before propagation to next stage
    def checkHazards(self, instruction, currentStage, nextStage): 
        hazards = []
        instruction = str(instruction)
        try:
            if nextStage != "END":
                if self.multipathPipeline[nextStage].full():  # structural hazard
                    hazards.append("STRUCT")
            if currentStage == "ID":
                if self.instructions[instruction]["opcode"].strip() in ["sw", "s.d"] or self.instructionSet[self.instructions[instruction]["opcode"]] == "NO_EX":
                    try:
                        if not self.register_status[self.instructions[instruction]["operands"][0].strip()]["W"] == 0:
                            hazards.append("RAW")
                    except:
                        pass
                if not self.register_status[self.instructions[instruction]["operands"][1].strip()]["W"] == 0:
                    hazards.append("RAW")
                if self.instructions[instruction]["opcode"].strip() not in ["sw", "s.d", "lw", "l.d"] and self.instructionSet[self.instructions[instruction]["opcode"]] != "NO_EX":
                    try:
                        if not self.register_status[self.instructions[instruction]["operands"][2].strip()]["W"] == 0:
                            hazards.append("RAW")
                    except:
                        pass
                if self.instructions[instruction]["opcode"] not in ["sw", "s.d"] and self.instructionSet[self.instructions[instruction]["opcode"]] != "NO_EX":
                    if not self.register_status[self.instructions[instruction]["operands"][0].strip()]["W"] == 0:
                        hazards.append("WAW")
#             
        except Exception as ex:
            pass
        finally:
            return hazards
    
    
    def enqueueInNextStage(self, instructionState, currentStage, nextStage):
        if currentStage == "ID":
            # set destination register operand status to write
            if instructionState[1].strip() not in ["sw", "s.d"] and self.instructionSet[instructionState[1]] != "NO_EX":
                self.register_status[self.instructions[str(instructionState[0][1])]["operands"][0].strip()]["W"] += 1
        
        # special check for no execution instructions
        if self.instructionSet[instructionState[1]] != "MEM" and nextStage == "MEM":
            self.multipathPipeline[nextStage].put(
                                              [
                                               instructionState[0],
                                               instructionState[1],
                                               0,
                                               instructionState[3]
                                               ]
                                              )
        elif nextStage == "MEM":
            # execute current stage actions for instruction
            instructionState = self.executeStageActions(instructionState, nextStage)
                                    
            # execute current stage actions for instruction
            self.multipathPipeline[nextStage].put(instructionState)
        else:
            self.multipathPipeline[nextStage].put(
                                              [
                                               instructionState[0],
                                               instructionState[1],
                                               self.multipathPipeline["CYCLE_TIMES"][nextStage] - 1,
                                               instructionState[3]
                                               ]
                                              )
    
    #updates the ouput table of each stage on completion
    def updateOutputTableStageCompletion(self, instructionIndex, currentStage):
        if currentStage == "INT_EX":
            pass
        elif currentStage in ["IF", "ID", "WB"]:
            self.outputTable[instructionIndex][currentStage] = self.clock - 1
        else:
            self.outputTable[instructionIndex]["EX"] = self.clock - 1
   
    #updates output table of Hazards        
    def updateOutputTableHazard(self, instructionIndex, hazards):
        for hazard in hazards:
            self.outputTable[instructionIndex][hazard] = True

    #lookup program counter in instruction cache
    def fetchInstruction(self, programCounter, outputIndex):
        # lookup program counter in instruction cache
        blockOffset = (programCounter - 1) % 4
        index = int((programCounter - 1) / 4) % 4
        
        if programCounter in self.instructionCache[index]:
            # cache hit
            self.instructionCacheHit += 1
            
            # return instruction state for fetch stage
            return [
                    [outputIndex, programCounter],
                    self.instructions[str(programCounter)]["opcode"],
                    int(self.pipelineConfiguration["i-cache"][0]) - 1,
                    [],
                    ["hit"]
                    ]
            
        # cache miss...program counter not in instruction cache
        self.instructionCacheMiss += 1
        
        # manage data bus contention
        if not self.dataBusInUse[0] or (self.dataBusInUse[0] and self.dataBusInUse[2] == self.clock):
            self.dataBusInUse = [True, outputIndex, self.clock]
        
        # load code memory block into instruction cache
        block = []
        blockStart = programCounter - blockOffset
        for instruction in range(blockStart, blockStart + 4):
            if instruction <= len(self.instructions):
                block.append(instruction)
            else:
                # garbage value
                block.append(-99)
        self.instructionCache[index] = block
                
        # return instruction state for fetch stage
        return [
                [outputIndex, programCounter],
                self.instructions[str(programCounter)]["opcode"],
                2 * (int(self.pipelineConfiguration["i-cache"][0]) + int(self.pipelineConfiguration["main memory"][0])) - 1,
                [],
                ["miss", self.clock]
                ]


    def executeStageActions(self, instructionState, currentStage):
        if not not re.search("\.d$", instructionState[1]) and self.instructionSet[instructionState[1]] != "MEM":
            return instructionState
        
        instructionContext = []
        if currentStage == "ID":
            # check if instruction is of no execution type (e.g control instructions)
            if self.instructionSet[instructionState[1]] == "NO_EX":
                if instructionState[1] in ["j", "beq", "bne"]:
                    # decode and execute branch
                    self.executeBranch(instructionState, instructionContext)
            else:
                # read registers
                self.readOperands(instructionState, instructionContext)
        elif currentStage == "INT_EX":
            # execute integer operation for arithmetic instructions
#             if not self.instructionSet[instructionState[1]] == "MEM":
            self.executeIntegerArithmetic(instructionState, instructionContext)
        elif currentStage == "MEM": 
            # execute memory operation for load/store instructions
            if self.instructionSet[instructionState[1]] == "MEM":
                self.executeMemoryOperation(instructionState)
        elif currentStage == "WB":
            # write back result in register for arithmetic instructions
            if (self.instructionSet[instructionState[1]] not in ["NO_EX"] 
                and 
                not re.search("\.d$", instructionState[1])):
                if not (self.instructionSet[instructionState[1]] == "MEM"
                        and
                        instructionState[1] != "lw"):
                    self.writeBackResult(instructionState)
            
        
        if len(instructionContext) == 0:
            return instructionState
        else:
            returnState = instructionState[:3]
            returnState.append(instructionContext)
            return returnState

    #Read operands
    def readOperands(self, instructionState, instructionContext): 
        for operand in self.instructions[str(instructionState[0][1])]["operands"][1:]:
            if re.search("^r", operand):
                instructionContext.append(self.registerFile[operand])
            else:
                instructionContext.append(int(operand))
    
    
    def executeBranch(self, instructionState, instructionContext):
        branchTakenLabel = ""
        if instructionState[1] == "j":
            # jump to label
            
            branchTakenLabel = self.instructions[str(instructionState[0][1])]["operands"][0]
            
            try:
                self.programCounter = int(self.labels[branchTakenLabel])
            except LookupError:
                print("Label \"" + self.instructions[str(instructionState[0][1])]["operands"][0] + "\" missing in instruction file.")
                raise Exception("Label \"" + self.instructions[str(instructionState[0][1])]["operands"][0] + "\" missing in instruction file.")
                    
            self.branchTaken = True
        else:
            # read register operands
            for operand in self.instructions[str(instructionState[0][1])]["operands"][:2]:
                if re.search("^r", operand):
                    instructionContext.append(self.registerFile[operand])
                else:
                    instructionContext.append(operand)
        
            # read branching label
            branchTakenLabel = self.instructions[str(instructionState[0][1])]["operands"][2]
            
            
            # evaluate branching decision
            if instructionState[1] == "bne":
                if instructionContext[0] != instructionContext[1]:
                    try:
                        self.programCounter = int(self.labels[branchTakenLabel])
                    except LookupError:
                        print("Label \"" + branchTakenLabel + "\" missing in instruction file.")
                        raise Exception("Label \"" + branchTakenLabel + "\" missing in instruction file.")
                    self.branchTaken = True
            elif instructionState[1] == "beq":
                if instructionContext[0] == instructionContext[1]:
                    try:
                        self.programCounter = int(self.labels[branchTakenLabel])
                    except LookupError:
                        print("Label \"" + branchTakenLabel + "\" missing in instruction file.")
                        raise Exception("Label \"" + branchTakenLabel + "\" missing in instruction file.")
                    
                    self.branchTaken = True            
            
    #Executes integer arithmetic operations based on the opcode
    def executeIntegerArithmetic(self, instructionState, instructionContext):
        if self.instructionSet[instructionState[1]] == "MEM":
            # add operands to obtaing effective memory address
            instructionContext.append(instructionState[3][0] + instructionState[3][1])
        elif instructionState[1] in ["dadd", "daddi"]:
            instructionContext.append(instructionState[3][0] + instructionState[3][1])
        elif instructionState[1] in ["dsub", "dsubi"]:
            instructionContext.append(instructionState[3][0] - instructionState[3][1])
        elif instructionState[1] in ["and", "andi"]:
            instructionContext.append(instructionState[3][0] & instructionState[3][1])
        elif instructionState[1] in ["or", "ori"]:
            instructionContext.append(instructionState[3][0] | instructionState[3][1])
    
    #This method executes the memory operations
    def executeMemoryOperation(self, instructionState):
        instructionState.append(["hit"])
        
        # access cache and set context to latency of operation 
        if self.lookupDataCache(instructionState[3][0]):
            # cache hit
            self.dataCacheHit += 1
            instructionState[2] = int(self.pipelineConfiguration["d-cache"][0]) - 1
            
        else:
            # cache miss
            self.dataCacheMiss += 1
            
            # manage data bus contention
            instructionState[4] = ["miss", self.clock]
            if not self.dataBusInUse[0]:
                self.dataBusInUse = [True, instructionState[0][0], self.clock]
            
            # insert looked up address in cache
            self.cacheMemoryAddress(instructionState[3][0])
            
            instructionState[2] = 2 * (int(self.pipelineConfiguration["d-cache"][0]) + 
                                       int(self.pipelineConfiguration["main memory"][0])) - 1
        
        if instructionState[1] in ["s.d", "l.d"]:
            # perform check for second word
            if self.lookupDataCache(int(instructionState[3][0]) + 4):
                # cache hit
                self.dataCacheHit += 1
                instructionState[2] += int(self.pipelineConfiguration["d-cache"][0])
            else:
                # cache miss
                self.dataCacheMiss += 1
                
                # manage data bus contention
                instructionState[4] = ["miss", self.clock]
                if not self.dataBusInUse[0]:
                    self.dataBusInUse = [True, instructionState[0][0], self.clock]
                
                # insert looked up address in cache
                self.cacheMemoryAddress(int(instructionState[3][0]) + 4)
                
                instructionState[2] += 2 * (int(self.pipelineConfiguration["d-cache"][0]) + 
                                           int(self.pipelineConfiguration["main memory"][0]))

        if instructionState[1] == "lw":
            # load instruction
            translatedAddress = (int(instructionState[3][0]) - 256) / 4
            memVal = self.dataMemory[str(translatedAddress)]
            instructionState[3] = [memVal]
        elif instructionState[1] == "sw":
            # store integer value at memory address
            translatedAddress = (int(instructionState[3][0]) - 256) / 4
            val = self.registerFile[self.instructions[str(instructionState[0][1])]["operands"][0]]
            self.dataMemory[str(translatedAddress)] = val
                                                  

    # lookup program counter in instruction cache
    def lookupDataCache(self, address):
        # lookup program counter in instruction cache
        blockOffset = int(address / 4) % 4
        cacheSet = int(int(address / 4) / 4) % 2
        
        
#         if len(self.dataCache[cacheSet]) == 0:
#             return False
        
        cacheIndex = 0
        for accessCount, cachedBlock in self.dataCache[cacheSet]:
            if address in cachedBlock:
                # cache hit
                self.dataCache[cacheSet][cacheIndex] = (accessCount + 1, cachedBlock)
                return True
            cacheIndex += 1
            
        # cache miss
        return False
        
    #Cache memory address
    def cacheMemoryAddress(self, address):
        
        blockOffset = int(address / 4) % 4
        cacheSet = int(int(address / 4) / 4) % 2
        block = []
        blockStart = address - (blockOffset * 4)
        for index in range(0, 4):
            cachedAddress = blockStart + (index * 4)
            block.append(cachedAddress)
            
        if len(self.dataCache[cacheSet]) != 2:
            heappush(self.dataCache[cacheSet], (1, block))
        else: 
            # cache full,replace least accessed cached address with new address
            heapreplace(self.dataCache[cacheSet], (1, block))
        
          
    def writeBackResult(self, instructionState):
        self.registerFile[self.instructions[str(instructionState[0][1])]["operands"][0]] = instructionState[3][0]
        
      
    def printOutputTable(self):
        print("INDEX\tINSTRUCTION\tIF\tID\tEX\tWB\tRAW\tWAW\tWAR\tSTRUCT")
        for outputIndex, outputVector in list(self.outputTable.items()):
            print(str(outputIndex) + "\t" + \
                    self.instructions[str(outputVector["INSTR"])]["opcode"] + " " + ",".join(map(str, self.instructions[str(outputVector["INSTR"])]["operands"])) + "\t" + \
                    str(outputVector["IF"]) + "\t" + \
                    str(outputVector["ID"]) + "\t" + \
                    str(outputVector["EX"]) + "\t" + \
                    str(outputVector["WB"]) + "\t" + \
                    str(outputVector["RAW"]) + "\t" + \
                    str(outputVector["WAW"]) + "\t" + \
                    str(outputVector["WAR"]) + "\t" + \
                    str(outputVector["STRUCT"]))
            
    def writeOutputFile(self, outputFilePath):
        instructionFile = io.open("./inst.txt")
        instruction = instructionFile.readline()
        instructions = []
        while instruction:
            instructions.append(instruction.strip())
            instruction = instructionFile.readline()
        
        outputFile = io.open(outputFilePath, "w")
        line = "\tINSTRUCTION\t\tIF\t\tID\t\tEX\t\tWB\t\tRAW\t\tWAW\t\tWAR\t\tSTRUCT" + "\n"
        outputFile.write(line)
        for outputIndex, outputVector in list(self.outputTable.items()):
            if len(instructions[outputVector["INSTR"] - 1]) <= 7:
                line = instructions[outputVector["INSTR"] - 1] + "\t\t\t"
            elif len(instructions[outputVector["INSTR"] - 1]) > 15:
                line = instructions[outputVector["INSTR"] - 1] + "\t\t"
            else:
                line = instructions[outputVector["INSTR"] - 1] + "\t\t"
                
            line += "\t" + (str(outputVector["IF"]) if outputVector["IF"] != 0 else "  ") + "\t\t" + \
                   (str(outputVector["ID"]) if outputVector["ID"] != 0 else "  ") + "\t\t" + \
                   (str(outputVector["EX"]) if outputVector["EX"] != 0 else "  ") + "\t\t" + \
                   (str(outputVector["WB"]) if outputVector["WB"] != 0 else "  ") + "\t\t" + \
                   ("Y" if outputVector["RAW"] else "N") + "\t\t" + \
                   ("Y" if outputVector["WAW"] else "N") + "\t\t" + \
                   ("Y" if outputVector["WAR"] else "N") + "\t\t" + \
                   ("Y" if outputVector["STRUCT"] else "N") + "\n"
            
            outputFile.write(line)
            
        outputFile.write("\nTotal number of access requests for instruction cache: " + str(self.instructionCacheHit + self.instructionCacheMiss))
        outputFile.write("\nNumber of instruction cache hits: " + str(self.instructionCacheHit))
        outputFile.write("\nTotal number of access requests for data cache: " + str(self.dataCacheHit + self.dataCacheMiss))
        outputFile.write("\nNumber of data cache hits: " + str(self.dataCacheHit))
        
        outputFile.close()
    
    
