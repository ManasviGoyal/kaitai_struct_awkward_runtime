// Select the test case by choosing the header and the test file
#include "index_option.h"
#define TESTFILE "../example_data/data/index_option.raw"

int main()
{
    std::string file_path = TESTFILE;
    void * builder = load(file_path);
    std::cout << "Execution completed" << std::endl;

    return 0;
}