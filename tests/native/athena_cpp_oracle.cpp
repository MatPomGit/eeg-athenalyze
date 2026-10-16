// Isolated native C++ regression harness derived from the Athena bit layout
// in BrainFlow muse_athena.cpp. NOT the native BrainFlow library or binary.
// Upstream source file blob SHA: 1fab5576dfc8483a61bca87105163f6ea755616c
// Constants: muse_athena_constants.h; µV=(raw-8192)*1450/16383.
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::string hex(argv[2]);
    const std::string tag(argv[1]);
    if ((tag != "11" && tag != "12") || hex.size() != 56) return 2;
    std::vector<uint8_t> data;
    for (size_t i = 0; i < hex.size(); i += 2) {
        const int hi=hex_digit(hex[i]), lo=hex_digit(hex[i+1]);
        if (hi < 0 || lo < 0) return 2;
        data.push_back(static_cast<uint8_t>(hi*16+lo));
    }
    const size_t channels = tag=="11" ? 4 : 8;
    const size_t rows = 16/channels;
    std::cout << std::setprecision(17);
    for (size_t t=0; t<rows; ++t) {
        for (size_t c=0; c<channels; ++c) {
            const size_t bit_start = (t*channels+c)*14;
            uint32_t raw=0;
            for (size_t k=0; k<14; ++k) {
                const size_t bit=bit_start+k;
                raw |= ((data[bit/8] >> (bit%8)) & 1u) << k;
            }
            const double uv=(static_cast<double>(raw)-8192.0)*(1450.0/16383.0);
            if (c) std::cout << " ";
            std::cout << raw << ":" << uv;
        }
        std::cout << "\n";
    }
    return 0;
}
