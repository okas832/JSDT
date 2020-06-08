# code_mutator

code_mutator takes js program as a string and manage mutation process

## gen_code()
generate code without mutation. Because gen_mutant not only change the operators but comments and line number of expression, replace original code with gen_code() and measure coverages.

## gen_mutant()
It generate randomly mutated code

## roll_back()
roll back code state to the previous one.