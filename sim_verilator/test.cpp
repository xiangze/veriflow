#include "test.h"
#include "verilated.h"

int main(int argc, char **argv, char **env) {
  Verilated::commandArgs(argc, argv);
  test* top = new test;

  while(!Verilated::gotFinish()) {
    top->eval();
  }

  delete top;

  exit(0);
}
