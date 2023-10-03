#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <fstream>
#include <iostream>
#include "../build/_deps/awkward-headers-src/layout-builder/awkward/LayoutBuilder.h"
#include "../src-animal/animal.h"

namespace py = pybind11;

/**
 * Create a snapshot of the given builder, and return an `ak.Array` pyobject
 * @tparam T type of builder
 * @param builder builder
 * @return pyobject of Awkward Array
 */
template<typename T>
py::object snapshot_builder(const T &builder) {
    // How much memory to allocate?
    std::map <std::string, size_t> names_nbytes = {};
    builder.buffer_nbytes(names_nbytes);

    // Allocate memory
    std::map<std::string, void *> buffers = {};
    for (auto it: names_nbytes) {
        uint8_t *ptr = new uint8_t[it.second];
        buffers[it.first] = (void *) ptr;
    }

    // Write non-contiguous contents to memory
    builder.to_buffers(buffers);
    auto from_buffers = py::module::import("awkward").attr("from_buffers");

    // Build Python dictionary containing arrays
    py::dict container;
    for (auto it: buffers) {

        py::capsule free_when_done(it.second, [](void *data) {
            uint8_t *dataPtr = reinterpret_cast<uint8_t *>(data);
            delete[] dataPtr;
        });

        uint8_t *data = reinterpret_cast<uint8_t *>(it.second);
        container[py::str(it.first)] = py::array_t<uint8_t>(
                {names_nbytes[it.first]},
                {sizeof(uint8_t)},
                data,
                free_when_done
        );
    }
    return from_buffers(builder.form(), builder.length(), container);
}

/**
 * Create array, and return its snapshot
 * @return pyobject of Awkward Array
 */
py::object load(std::string file_path) {
    std::ifstream infile(file_path, std::ifstream::binary);
    kaitai::kstream ks(&infile);
    animal_t zoo = animal_t(&ks);
    return snapshot_builder(zoo.animal_builder);
}

PYBIND11_MODULE(awkward_animal, m) {
    m.def("load", &load);
}