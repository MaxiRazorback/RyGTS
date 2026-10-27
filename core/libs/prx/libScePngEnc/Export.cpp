// libScePngEnc: PNG encoding for games that save pictures (GT Sport writes PNGs for its photo and
// livery thumbnails). Used when the firmware's own libScePngEnc module is not in the system
// modules folder; with it, the loader runs the firmware module instead. The previous stubs
// returned 0 everywhere ("success" with no handle and an empty picture), and GT Sport crashed
// in its file thread soon after on fresh saves.
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <vector>
#include "SceTypes.hpp"

#define STBI_WRITE_NO_STDIO
#define STB_IMAGE_WRITE_STATIC
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "../../../../3rdparty/stb/stb_image_write.h"

namespace {

constexpr int32_t ERROR_INVALID_ADDR = static_cast<int32_t>(0x80690101);
constexpr int32_t ERROR_INVALID_SIZE = static_cast<int32_t>(0x80690102);
constexpr int32_t ERROR_INVALID_PARAM = static_cast<int32_t>(0x80690103);
constexpr int32_t ERROR_INVALID_HANDLE = static_cast<int32_t>(0x80690104);
constexpr int32_t ERROR_DATA_OVERFLOW = static_cast<int32_t>(0x80690110);
constexpr int32_t ERROR_FATAL = static_cast<int32_t>(0x80690120);

constexpr uint32_t MAX_IMAGE_WIDTH = 1000000;
constexpr uint32_t HANDLE_MAGIC = 0x50454e43; // "PENC"

constexpr uint16_t PIXEL_FORMAT_B8G8R8A8 = 1;
constexpr uint16_t COLOR_SPACE_RGB = 3;
constexpr uint16_t COLOR_SPACE_RGBA = 19;

struct PngEncCreateParam {
    uint32_t this_size;
    uint32_t attribute;
    uint32_t max_image_width;
    uint32_t max_filter_number;
};

struct PngEncEncodeParam {
    const uint8_t* image_mem_addr;
    uint8_t* png_mem_addr;
    uint32_t image_mem_size;
    uint32_t png_mem_size;
    uint32_t image_width;
    uint32_t image_height;
    uint32_t image_pitch;
    uint16_t pixel_format;
    uint16_t color_space;
    uint16_t bit_depth;
    uint16_t clut_number;
    uint16_t filter_type;
    uint16_t compression_level;
};

struct PngEncOutputInfo {
    uint32_t data_size;
    uint32_t processed_height;
};

struct Handle {
    uint32_t magic;
    uint32_t max_image_width;
};

static_assert(sizeof(PngEncCreateParam) == 0x10);
static_assert(sizeof(PngEncEncodeParam) == 0x30);
static_assert(sizeof(PngEncOutputInfo) == 0x8);

} // namespace

extern "C" {

int32_t APS5_VABI scePngEncQueryMemorySize(const PngEncCreateParam* param) {
    if (param == nullptr) {
        return ERROR_INVALID_ADDR;
    }
    if (param->attribute != 0 || param->max_filter_number > 5) {
        return ERROR_INVALID_PARAM;
    }
    if (param->max_image_width - 1 > MAX_IMAGE_WIDTH) {
        return ERROR_INVALID_SIZE;
    }
    return static_cast<int32_t>(sizeof(Handle));
}

int32_t APS5_VABI scePngEncCreate(const PngEncCreateParam* param, void* memory_address,
                                  uint32_t memory_size, void** handle) {
    if (param == nullptr || memory_address == nullptr || handle == nullptr) {
        return ERROR_INVALID_ADDR;
    }
    if (param->attribute != 0) {
        return ERROR_INVALID_PARAM;
    }
    if (param->max_image_width - 1 > MAX_IMAGE_WIDTH || memory_size < sizeof(Handle)) {
        return ERROR_INVALID_SIZE;
    }
    auto* h = static_cast<Handle*>(memory_address);
    h->magic = HANDLE_MAGIC;
    h->max_image_width = param->max_image_width;
    *handle = h;
    return 0;
}

int32_t APS5_VABI scePngEncDelete(void* handle) {
    auto* h = static_cast<Handle*>(handle);
    if (h == nullptr || h->magic != HANDLE_MAGIC) {
        return ERROR_INVALID_HANDLE;
    }
    h->magic = 0;
    return 0;
}

int32_t APS5_VABI scePngEncEncode(void* handle, const PngEncEncodeParam* param,
                                  PngEncOutputInfo* output_info) {
    const auto* h = static_cast<const Handle*>(handle);
    if (h == nullptr || h->magic != HANDLE_MAGIC) {
        return ERROR_INVALID_HANDLE;
    }
    if (param == nullptr) {
        return ERROR_INVALID_PARAM;
    }
    if (param->image_mem_addr == nullptr || param->png_mem_addr == nullptr) {
        return ERROR_INVALID_ADDR;
    }
    if (param->png_mem_size == 0 || param->image_mem_size == 0 || param->image_width == 0 ||
        param->image_height == 0 || param->image_width > h->max_image_width) {
        return ERROR_INVALID_SIZE;
    }
    if (param->bit_depth != 8 ||
        (param->color_space != COLOR_SPACE_RGB && param->color_space != COLOR_SPACE_RGBA)) {
        return ERROR_INVALID_PARAM;
    }
    static bool logged = false;
    if (!logged) {
        // GT Sport: 400x225 RGBA, all filters, level 6, for the new car's garage thumbnail.
        logged = true;
        std::fprintf(stderr, "[PngEnc] encoding %ux%u (HLE encoder, no firmware module)\n",
                     param->image_width, param->image_height);
    }
    const uint32_t width = param->image_width;
    const uint32_t height = param->image_height;
    const uint32_t pitch = param->image_pitch != 0 ? param->image_pitch : width * 4;
    if (pitch < width * 4 || uint64_t(pitch) * (height - 1) + width * 4ull > param->image_mem_size) {
        return ERROR_INVALID_SIZE;
    }
    // The input is always 4 bytes a pixel; the output drops alpha for RGB and swaps BGRA.
    const int channels = param->color_space == COLOR_SPACE_RGBA ? 4 : 3;
    const bool bgra = param->pixel_format == PIXEL_FORMAT_B8G8R8A8;
    std::vector<uint8_t> pixels(size_t(width) * height * channels);
    for (uint32_t y = 0; y < height; ++y) {
        const uint8_t* src = param->image_mem_addr + size_t(y) * pitch;
        uint8_t* dst = pixels.data() + size_t(y) * width * channels;
        for (uint32_t x = 0; x < width; ++x, src += 4, dst += channels) {
            dst[0] = bgra ? src[2] : src[0];
            dst[1] = src[1];
            dst[2] = bgra ? src[0] : src[2];
            if (channels == 4) {
                dst[3] = src[3];
            }
        }
    }
    stbi_write_png_compression_level = std::clamp<int>(param->compression_level, 1, 9);
    int length = 0;
    unsigned char* png = stbi_write_png_to_mem(pixels.data(), int(width) * channels, int(width),
                                               int(height), channels, &length);
    if (png == nullptr || length <= 0) {
        std::free(png);
        return ERROR_FATAL;
    }
    if (uint32_t(length) > param->png_mem_size) {
        std::free(png);
        if (output_info != nullptr) {
            output_info->data_size = 0;
            output_info->processed_height = 0;
        }
        return ERROR_DATA_OVERFLOW;
    }
    std::memcpy(param->png_mem_addr, png, size_t(length));
    std::free(png);
    if (output_info != nullptr) {
        output_info->data_size = uint32_t(length);
        output_info->processed_height = height;
    }
    return length;
}

}
