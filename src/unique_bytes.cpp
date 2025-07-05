#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <unordered_set>

namespace py = pybind11;

// Function that counts unique byte sequences (chunks) of length 'chunk_size'
// in a binary string provided as a py::bytes object.
size_t count_unique_chunks(py::bytes data, size_t chunk_size) {
    // Convert the Python bytes object to a std::string.
    std::string s = data;
    size_t data_size = s.size();

    if (chunk_size <= 0 || static_cast<size_t>(chunk_size) > data_size) {
        throw std::invalid_argument("Invalid chunk size: " +
                                    std::to_string(chunk_size));
    }

    if (data_size % chunk_size != 0) {
        throw std::invalid_argument(
            "Data size must be a multiple of chunk size");
    }

    std::unordered_set<std::string> unique;
    for (size_t i = 0; i < data_size; i += chunk_size) {
        unique.insert(s.substr(i, chunk_size));
    }

    return unique.size();
}

size_t _get_index_of(size_t size, int chunk_size,
                     std::pair<size_t, size_t> point) {
    return chunk_size * (point.first * size + point.second);
}

// We regard data as a grid of width and height size, where each node has a
// value of with bytes chunk_size.
// This function should always return the same value as count_unique_chunks.
// This function should be much more efficient than count_unique_chunks,
// since it uses the fact that regions are cuboids.
namespace count_regions {
void _count_subregion(std::unordered_set<std::string> &unique,
                      const std::string &s, std::pair<size_t, size_t> corner,
                      size_t subSize, size_t size, size_t chunk_size) {
    size_t startIndex = _get_index_of(size, chunk_size, corner);
    if (subSize <= 2) {
        for (size_t i = 0; i < subSize; ++i) {
            for (size_t j = 0; j < subSize; ++j) {
                size_t index = _get_index_of(
                    size, chunk_size, {corner.first + i, corner.second + j});
                unique.insert(s.substr(index, chunk_size));
            }
        }
        // Base case: add the single chunk at the corner to the set.
        unique.insert(s.substr(startIndex, chunk_size));
        return;
    } else {
        size_t endIndex = _get_index_of(
            size, chunk_size,
            {corner.first + subSize - 1, corner.second + subSize - 1});
        if (s.substr(startIndex, chunk_size) ==
            s.substr(endIndex, chunk_size)) {
            unique.insert(s.substr(startIndex, chunk_size));
        } else {
            // Recursive case: divide the region into four quadrants.
            size_t halfSize = subSize / 2;
            _count_subregion(unique, s, {corner.first, corner.second}, halfSize,
                             size, chunk_size);
            _count_subregion(unique, s,
                             {corner.first, corner.second + halfSize}, halfSize,
                             size, chunk_size);
            _count_subregion(unique, s,
                             {corner.first + halfSize, corner.second}, halfSize,
                             size, chunk_size);
            _count_subregion(
                unique, s, {corner.first + halfSize, corner.second + halfSize},
                halfSize, size, chunk_size);
        }
    }
}

bool _is_power_of_two(int x) { return x > 0 && (x & (x - 1)) == 0; }

size_t count_regions(py::bytes data, size_t size, size_t chunk_size) {
    std::string s = data;
    size_t data_size = s.size();

    if (chunk_size <= 0) {
        throw std::invalid_argument("Invalid chunk size: " +
                                    std::to_string(chunk_size));
    }

    if (size <= 0) {
        throw std::invalid_argument("Invalid size: " +
                                    std::to_string(chunk_size));
    }

    if (data_size != size * size * chunk_size) {
        throw std::invalid_argument(
            "Data byte count must be equal to size * size * chunk_size");
    }

    if (!_is_power_of_two(size)) {
        throw std::invalid_argument("Size must be a power of two");
    }

    std::unordered_set<std::string> unique;
    _count_subregion(unique, s, {0, 0}, size, size, chunk_size);
    return unique.size();
}
} // namespace count_regions

// search last element with same value as start until end in s
// values are have size chunk_size
size_t search_steps(std::string &s, size_t chunk_size, size_t start, size_t end,
                    size_t stepSize) {
    size_t d = 0;
    size_t n = 0;
    while (true) {
        size_t nextD = d + (1 << n);
        size_t nextIndex = start + nextD * stepSize;
        if ((nextIndex < end) &&
            (std::memcmp(s.data() + nextIndex, s.data() + start, chunk_size) ==
             0)) {
            d = nextD;
            n++;
        } else {
            // if n == 0 we found the last node with same value as
            // (i,j)
            if (n == 0) {
                break;
            } else {
                n--;
            }
        }
    }
    return d;
}

std::vector<py::bytes> unique_regions(py::bytes data, size_t size,
                                      size_t chunk_size) {
    std::string s = data;
    size_t data_size = s.size();

    if (chunk_size <= 0) {
        throw std::invalid_argument("Invalid chunk size: " +
                                    std::to_string(chunk_size));
    }

    if (size <= 0) {
        throw std::invalid_argument("Invalid size: " +
                                    std::to_string(chunk_size));
    }

    if (data_size != size * size * chunk_size) {
        throw std::invalid_argument(
            "Data byte count must be equal to size * size * chunk_size");
    }

    // valueMap captures if the value of a certain element in s
    // has already been added to values.
    // If that is the case, valueMap has the index of the value in values.
    std::vector<int> valueMap(s.size() / chunk_size, -1);
    std::vector<py::bytes> values{};

    for (size_t i = 0; i < size; ++i) {
        for (size_t j = 0; j < size; ++j) {
            size_t indexVM = i * size + j;
            // check if value has already been added to values
            if (valueMap[indexVM] == -1) {
                // find the width dx and height dy of the region with the
                // same value
                size_t dx =
                    1 + search_steps(s, chunk_size,
                                     _get_index_of(size, chunk_size, {i, j}),
                                     _get_index_of(size, chunk_size, {size, j}),
                                     size * chunk_size);
                size_t dy =
                    1 + search_steps(s, chunk_size,
                                     _get_index_of(size, chunk_size, {i, j}),
                                     _get_index_of(size, chunk_size, {i, size}),
                                     chunk_size);
                values.push_back(s.substr(
                    _get_index_of(size, chunk_size, {i, j}), chunk_size));
                int valueIndex = values.size();
                for (size_t k = 0; k < dx; ++k) {
                    for (size_t l = 0; l < dy; ++l) {
                        valueMap[(i + k) * size + (j + l)] = valueIndex;
                    }
                }
            }
        }
    }

    return values;
}

std::vector<py::bytes> llcorner_values(py::bytes data, size_t size,
                                       size_t chunk_size) {
    std::string s = data;
    size_t data_size = s.size();

    if (chunk_size <= 0) {
        throw std::invalid_argument("Invalid chunk size: " +
                                    std::to_string(chunk_size));
    }

    if (size <= 0) {
        throw std::invalid_argument("Invalid size: " +
                                    std::to_string(chunk_size));
    }

    if (data_size != size * size * chunk_size) {
        throw std::invalid_argument(
            "Data byte count must be equal to size * size * chunk_size");
    }

    std::vector<py::bytes> values{};

    for (size_t i = 0; i < size; ++i) {
        for (size_t j = 0; j < size; ++j) {
            // Check if the value at the current position is different
            // from the value to the left and below it.
            bool leftIsDiff =
                i == 0 ||
                (std::memcmp(s.data() + _get_index_of(size, chunk_size, {i, j}),
                             s.data() +
                                 _get_index_of(size, chunk_size, {i - 1, j}),
                             chunk_size) != 0);
            bool belowIsDiff =
                j == 0 ||
                (std::memcmp(s.data() + _get_index_of(size, chunk_size, {i, j}),
                             s.data() +
                                 _get_index_of(size, chunk_size, {i, j - 1}),
                             chunk_size) != 0);
            // If it is different indeed, the current position is a ll corner of
            // a region.
            if (leftIsDiff && belowIsDiff) {
                values.push_back(s.substr(
                    _get_index_of(size, chunk_size, {i, j}), chunk_size));
            }
        }
    }

    return values;
}

int llcorner_uniques(py::bytes data, size_t size, size_t chunk_size) {
    std::string s = data;
    size_t data_size = s.size();

    if (chunk_size <= 0) {
        throw std::invalid_argument("Invalid chunk size: " +
                                    std::to_string(chunk_size));
    }

    if (size <= 0) {
        throw std::invalid_argument("Invalid size: " +
                                    std::to_string(chunk_size));
    }

    if (data_size != size * size * chunk_size) {
        throw std::invalid_argument(
            "Data byte count must be equal to size * size * chunk_size");
    }

    int valuesN = 0;

    for (size_t i = 0; i < size; ++i) {
        for (size_t j = 0; j < size; ++j) {
            // Check if the value at the current position is different
            // from the value to the left and below it.
            bool leftIsDiff =
                i == 0 ||
                (std::memcmp(s.data() + _get_index_of(size, chunk_size, {i, j}),
                             s.data() +
                                 _get_index_of(size, chunk_size, {i - 1, j}),
                             chunk_size) != 0);
            bool belowIsDiff =
                j == 0 ||
                (std::memcmp(s.data() + _get_index_of(size, chunk_size, {i, j}),
                             s.data() +
                                 _get_index_of(size, chunk_size, {i, j - 1}),
                             chunk_size) != 0);
            // If it is different indeed, the current position is a ll corner of
            // a region.
            if (leftIsDiff && belowIsDiff) {
                valuesN++;
            }
        }
    }

    return valuesN;
}

PYBIND11_MODULE(unique_bytes, m) {
    m.doc() = "Module for counting unique fixed-length byte sequences from a "
              "binary string";
    m.def("count_unique_chunks", &count_unique_chunks, py::arg("data"),
          py::arg("chunk_size"),
          "Count unique chunks in the given bytes object with the specified "
          "chunk_size");
    m.def("count_regions", &count_regions::count_regions, py::arg("data"),
          py::arg("size"), py::arg("chunk_size"),
          "Count unique regions in the given bytes object with the "
          "specified size and chunk_size");
    m.def("unique_regions", &unique_regions, py::arg("data"), py::arg("size"),
          py::arg("chunk_size"),
          "Get unique regions in the given bytes object with the "
          "specified size and chunk_size");
    m.def("llcorner_values", &llcorner_values, py::arg("data"), py::arg("size"),
          py::arg("chunk_size"),
          "Get the values of the lower-left corners of unique regions in the "
          "given bytes object with the specified size and chunk_size"
          "Only works for cuboids regions.");
    m.def("llcorner_uniques", &llcorner_uniques, py::arg("data"),
          py::arg("size"), py::arg("chunk_size"),
          "Count the number of unique lower-left corners in the given bytes "
          "object with the specified size and chunk_size"
          "Only works for cuboids regions.");
}
