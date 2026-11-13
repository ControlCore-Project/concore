// Header smoke test for concore.hpp. Verifies the file is self-contained
// and Concore is a complete type without needing any system SHM calls.

#include "concore.hpp"

int main() {
    static_assert(sizeof(Concore) > 0, "Concore must be a complete type");
    return 0;
}
