import sys
import subprocess
import numpy as np
import random

# read the sudoku file
def sudoku_read(filename):
    myfile = open(filename, 'r')
    sudoku = []
    N = 0
    for line in myfile:
        line = line.replace(" ", "")
        if line == "":
            continue
        line = line.split("|")
        if line[0] != '':
            exit("illegal input: every line should start with |\n")
        line = line[1:]
        if line.pop() != '\n':
            exit("illegal input\n")
        if N == 0:
            N = len(line)
            if N not in [4, 9, 16, 25]:
                exit("illegal input: only size 4, 9, 16 and 25 are supported\n")
        elif N != len(line):
            exit("illegal input: number of columns not invariant\n")
        line = [int(x) if x != '' and int(x) >= 0 and int(x) <= N else 0 for x in line]
        sudoku += [line]
    return sudoku

# print the sudoku
def sudoku_print(myfile, sudoku):
    if sudoku == []:
        myfile.write("impossible sudoku\n")
    N = len(sudoku)
    for line in sudoku:
        myfile.write("|")
        for number in line:
            if N > 9 and number < 10:
                myfile.write(" ")
            myfile.write(" " if number == 0 else str(number))
            myfile.write("|")
        myfile.write("\n")

# get number of constraints for sudoku
def sudoku_constraints_number(sudoku):
    N = len(sudoku)
    # Here generate the number of constraints
    clues=0
    for row in range(N):
        for column in range(N):
            if sudoku[row][column]>0:
                clues=clues+1                    
    binary_clauses= (N**2)*(N*(N-1)/2)            
    n_clauses= 3*(N**2)   
    count = n_clauses+binary_clauses+clues
    return int(count)

def give_n(N):
    if N == 4:
        n = 2
    elif N == 9:
        n = 3
    elif N == 16:
        n = 4
    elif N == 25:
        n = 5
    else:
        exit("Only supports size 4, 9, 16 and 25")
    return n

# prints the generic constraints for sudoku of size N
def sudoku_generic_constraints(myfile, N):
    n=give_n(N)

    def output(s):
        myfile.write(s)

    def newlit(i,j,k): # OR 
        output(str(N**2*(i-1)+N*(j-1)+k)+ " ")

    def newneglit(i,j,k): # OR (Negative) 
        output("-"+str(N**2*(i-1)+N*(j-1)+k)+ " ")

    def newcl(): # AND
        output("0\n")

    #Constraints re-ordered to fit the same model as the given one
    # Constraint 1: At most one number in each entry
    for row in range(1,N+1):
        for column in range(1,N+1):
            for value in range(1,N):
                for auxvalue in range(value+1,N+1):
                    newneglit(row,column,value)
                    newneglit(row,column,auxvalue)
                    newcl()

    # Constraint 4: Each number at least once per sub-grid
    for plusrow in range(0,n): 
        for pluscolumn in range(0,n):
            for value in range(1,N+1):
                for row in range(1,n+1):
                    for column in range(1,n+1):
                        newlit((n*plusrow+row),(n*pluscolumn+column),value)
                newcl()                                                 

    # Constraint 3: Each number at least once per column
    for row in range(1,N+1):
        for value in range(1,N+1):
            for column in range(1,N+1):
                newlit(row,column,value)
            newcl()

    # Constraint 2: Each number at least once per row
    for column in range(1,N+1):
        for value in range(1,N+1):
            for row in range(1,N+1):
                newlit(row,column,value)
            newcl()
                   
# prints the specific constraints for sudoku of size N (clues)
def sudoku_specific_constraints(myfile, sudoku):
    N = len(sudoku)

    def output(s):
        myfile.write(s)

    def newlit(i,j,k):
        output(str(N**2*(i-1)+N*(j-1)+k)+ " ")

    def newcl():
        output("0\n")

    # Constraint 5: Clues
    for i in range(N):
        for j in range(N):
            if sudoku[i][j] > 0:
                newlit(i+1, j+1, sudoku[i][j])
                newcl()

# checks if there is another solution
def sudoku_other_solution_constraint(myfile, sudoku, sudokusol):
    N = len(sudoku)

    def output(s):
        myfile.write(s)

    def newneglit(i,j,k):
        output("-"+str(N**2*(i-1)+N*(j-1)+k)+ " ")

    def newcl():
        output("0\n")

    # Negate current solution
    for row in range(1,N+1):
        for column in range(1,N+1):
            if sudoku[row-1][column-1]==0:
                newneglit(row,column,sudokusol[row-1][column-1])
    newcl()  
    
                
def sudoku_solve(filename):
    command = "java -jar org.sat4j.core.jar "+filename
    process = subprocess.Popen(command, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    for line in out.split(b'\n'):
        line = line.decode("utf-8")
        if line == "" or line[0] == 'c':
            continue
        if line[0] == 's':
            if (line[2]!='S') or (line[3]!='A'):           
                return []
            continue
        if line[0] == 'v':
            line = line[2:]
            units = line.split()
            if units.pop() != '0':
                exit("strange output from SAT solver:" + line + "\n")
            units = [int(x) for x in units if int(x) >= 0]
            N = len(units)
            if N == 16:
                N = 4
            elif N == 81:
                N = 9
            elif N == 256:
                N = 16
            elif N == 625:
                N = 25
            else:
                exit("strange output from SAT solver:" + line + "\n")
            sudoku = [ [0 for i in range(N)] for j in range(N)]

            for number in units:
                row=number//(N**2)
                column=(number//N) % N  
                value=number % N

                if value==0:
                    value=N
                    if column==0:
                        row=row-1
                        column=N-1
                    else:
                        column=column-1

                sudoku[row][column]=value

            return sudoku
        exit("strange output from SAT solver:" + line + "\n")
        return []

def sudoku_othersolution(filename, sudoku, sudokusol):
    myfile = open(filename, 'a')
    sudoku_other_solution_constraint(myfile, sudoku, sudokusol)
    myfile.close()
    sudokusol2 = sudoku_solve(filename)
    return sudokusol2

def sudoku_filler(N): 
    n=give_n(N)                  

    #Create empty sudoku
    sudokugen=np.zeros((N,N), dtype=int)

    #Create lists for the possible values   
    row_possible = list(range(N))
    column_possible = list(range(N))
    subgrid_possible=[]
    for _ in range(N): 
        subgridvalue = list(range(1,N+1)) #Possible values inside a subgrid
        subgrid_possible.append(subgridvalue) 

    #Fill with some random numbers
    keepgenerating=True
    while keepgenerating:
        #Generate first random number
        row=random.choice(row_possible)
        column=random.choice(column_possible)
        subgridnum=(column//n)+(row//n)*n
        value=random.choice(subgrid_possible[subgridnum])

        #Insert the value
        sudokugen[row][column]=value

        #Remove from possible ones
        row_possible.remove(row)
        column_possible.remove(column)
        subgridnum=(column//n)+(row//n)*n
        subgrid_possible[subgridnum].remove(value) 

        #Check if its possible to continue
        if not row_possible or not column_possible or not subgrid_possible:
            keepgenerating=False

    #Now that the sudoku has some clues, we have to solve it
    filename="sudokugen.cnf"
    sudoku_filecreation(filename, sudokugen, N)
    sudokugen = sudoku_solve(filename)
    sys.stdout.write("\nunique solution\n")
    sudoku_print(sys.stdout, sudokugen)
    return sudokugen 

def sudoku_blank(sudokugen, N):
    #Create list with all the values in the sudoku encoded
    options=[]
    for row in range(len(sudokugen)):
        for column in range(len(sudokugen[row])):
            options.append(N**2*(row)+N*(column)+sudokugen[row][column])           

    while len(options)!=0:
        #Generate random position
        choice=random.choice(options)
        options.remove(choice)

        row=choice//(N**2)
        column=(choice//N) % N
        value=choice % N

        if value==0:
            value=N
            if column==0:
                row=row-1
                column=N-1
            else:
                column=column-1

        #Delete the value in that random position
        sudokugen[row][column]=0
        #Check if there is only one solution        
        filename="sudoku_blank.cnf"
        sudoku_filecreation(filename,sudokugen,N)
        firstsolution=sudoku_solve(filename)
        secondsolution=sudoku_othersolution(filename,sudokugen,firstsolution)
        if secondsolution!=[]:
            sudokugen[row][column]=value

    return sudokugen

def sudoku_generate(N):
    sudokugen=sudoku_filler(N) #Function to generate a sudoku
    sudoku=sudoku_blank(sudokugen, N) #Function to remove numbers of a sudoku
    return sudoku

def sudoku_filecreation(filename,sudoku,N):
    myfile = open(filename, 'w')
    myfile.write("p cnf ")
    if(N==16):
        myfile.write("5832")
    elif(N==25):
        myfile.write("19683")
    else:
        myfile.write(str(N)+str(N)+str(N))
    myfile.write(" "+str(sudoku_constraints_number(sudoku))+"\n")
    sudoku_generic_constraints(myfile, N)
    sudoku_specific_constraints(myfile, sudoku)
    myfile.close()
    
from enum import Enum
class Mode(Enum):
    SOLVE = 1
    UNIQUE = 2
    CREATE = 3
    CREATEMIN = 4

OPTIONS = {}
OPTIONS["-s"] = Mode.SOLVE
OPTIONS["-u"] = Mode.UNIQUE
OPTIONS["-c"] = Mode.CREATE
OPTIONS["-cm"] = Mode.CREATEMIN

if len(sys.argv) != 3 or not sys.argv[1] in OPTIONS :
    sys.stdout.write("./sudokub.py <operation> <argument>\n")
    sys.stdout.write("     where <operation> can be -s, -u, -c, -cm\n")
    sys.stdout.write("  ./sudokub.py -s <input>.txt: solves the Sudoku in input, whatever its size\n")
    sys.stdout.write("  ./sudokub.py -u <input>.txt: check the uniqueness of solution for Sudoku in input, whatever its size\n")
    sys.stdout.write("  ./sudokub.py -c <size>: creates a Sudoku of appropriate <size>\n")
    sys.stdout.write("  ./sudokub.py -cm <size>: creates a Sudoku of appropriate <size> using only <size>-1 numbers\n")
    sys.stdout.write("    <size> is either 4, 9, 16, or 25\n")
    exit("Bad arguments\n")

mode = OPTIONS[sys.argv[1]]
if mode == Mode.SOLVE or mode == Mode.UNIQUE:
    filename = str(sys.argv[2])
    sudoku = sudoku_read(filename)
    N = len(sudoku)
    sudoku_filecreation("sudoku.cnf", sudoku, N)
    sys.stdout.write("sudoku\n")
    sudoku_print(sys.stdout, sudoku)
    sudokusol = sudoku_solve("sudoku.cnf")    
    sys.stdout.write("\nsolution\n")
    sudoku_print(sys.stdout, sudokusol)
    if sudokusol != [] and mode == Mode.UNIQUE:
        sudokusol2=sudoku_othersolution("sudoku.cnf", sudoku, sudokusol)
        if sudokusol2 == []:
            sys.stdout.write("\nsolution is unique\n")
        else:
            sys.stdout.write("\nother solution\n")
            sudoku_print(sys.stdout, sudokusol2)
elif mode == Mode.CREATE:
    size = int(sys.argv[2])
    sudoku = sudoku_generate(size)
    sys.stdout.write("\ngenerated sudoku\n")
    sudoku_print(sys.stdout, sudoku)
elif mode == Mode.CREATEMIN:
    size = int(sys.argv[2])
    sudoku = sudoku_generate(size)
    sys.stdout.write("\ngenerated sudoku\n")
    sudoku_print(sys.stdout, sudoku)
