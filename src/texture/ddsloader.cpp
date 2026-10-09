// SPDX-License-Identifier: BSD-3-Clause
// https://github.com/OpenImageIO/oiio/blob/master/LICENSE.md

#include <string>

#include "../log.h"

#include "ddsloader.h"

#include <squish/squish.h>

using namespace Impacto::Io;

namespace Impacto {
namespace Gxm {
// IneQuation was here

#define DDS_MAKE4CC(a, b, c, d) (a | b << 8 | c << 16 | d << 24)
#define DDS_4CC_DXT1 DDS_MAKE4CC('D', 'X', 'T', '1')
#define DDS_4CC_DXT2 DDS_MAKE4CC('D', 'X', 'T', '2')
#define DDS_4CC_DXT3 DDS_MAKE4CC('D', 'X', 'T', '3')
#define DDS_4CC_DXT4 DDS_MAKE4CC('D', 'X', 'T', '4')
#define DDS_4CC_DXT5 DDS_MAKE4CC('D', 'X', 'T', '5')

/// DDS pixel format flags. Channel flags are only applicable for uncompressed
/// images.
///
enum {
  DDS_PF_ALPHA = 0x00000001,      ///< image has alpha channel
  DDS_PF_FOURCC = 0x00000004,     ///< image is compressed
  DDS_PF_LUMINANCE = 0x00020000,  ///< image has luminance data
  DDS_PF_RGB = 0x00000040         ///< image has RGB data
};

/// DDS pixel format structure.
///
typedef struct {
  uint32_t size;    ///< structure size, must be 32
  uint32_t flags;   ///< flags to indicate valid fields
  uint32_t fourCC;  ///< compression four-character code
  uint32_t bpp;     ///< bits per pixel
  uint32_t rmask;   ///< bitmask for the red channel
  uint32_t gmask;   ///< bitmask for the green channel
  uint32_t bmask;   ///< bitmask for the blue channel
  uint32_t amask;   ///< bitmask for the alpha channel
} dds_pixformat;

/// DDS caps flags, field 1.
///
enum {
  DDS_CAPS1_COMPLEX = 0x00000008,  ///< >2D image or cube map
  DDS_CAPS1_TEXTURE = 0x00001000,  ///< should be set for all DDS files
  DDS_CAPS1_MIPMAP = 0x00400000    ///< image has mipmaps
};

/// DDS caps flags, field 2.
///
enum {
  DDS_CAPS2_CUBEMAP = 0x00000200,            ///< image is a cube map
  DDS_CAPS2_CUBEMAP_POSITIVEX = 0x00000400,  ///< +x side
  DDS_CAPS2_CUBEMAP_NEGATIVEX = 0x00000800,  ///< -x side
  DDS_CAPS2_CUBEMAP_POSITIVEY = 0x00001000,  ///< +y side
  DDS_CAPS2_CUBEMAP_NEGATIVEY = 0x00002000,  ///< -y side
  DDS_CAPS2_CUBEMAP_POSITIVEZ = 0x00004000,  ///< +z side
  DDS_CAPS2_CUBEMAP_NEGATIVEZ = 0x00008000,  ///< -z side
  DDS_CAPS2_VOLUME = 0x00200000              ///< image is a 3D texture
};

/// DDS caps structure.
///
typedef struct {
  uint32_t flags1;  ///< flags to indicate certain surface properties
  uint32_t flags2;  ///< flags to indicate certain surface properties
} dds_caps;

/// DDS global flags - indicate valid header fields.
///
enum {
  DDS_CAPS = 0x00000001,
  DDS_HEIGHT = 0x00000002,
  DDS_WIDTH = 0x00000004,
  DDS_PITCH = 0x00000008,
  DDS_PIXELFORMAT = 0x00001000,
  DDS_MIPMAPCOUNT = 0x00020000,
  DDS_LINEARSIZE = 0x00080000,
  DDS_DEPTH = 0x00800000
};

/// DDS file header.
/// Please note that this layout is not identical to the one found in a file.
///
typedef struct {
  uint32_t fourCC;   ///< file four-character code
  uint32_t size;     ///< structure size, must be 124
  uint32_t flags;    ///< flags to indicate valid fields
  uint32_t height;   ///< image height
  uint32_t width;    ///< image width
  uint32_t pitch;    ///< bytes per scanline (uncmp.)/total byte size (cmp.)
  uint32_t depth;    ///< image depth (for 3D textures)
  uint32_t mipmaps;  ///< number of mipmaps
  // 11 reserved 4-byte fields come in here
  dds_pixformat fmt;  ///< pixel format
  dds_caps caps;      ///< DirectDraw Surface caps
} dds_header;

// Profile::LoadSpritesheets decodes textures concurrently using std::async.
// Keep metadata local to a single load, never shared between decoder threads.
struct DdsDecodeState {
  dds_header dds{};
  int nchans = 0;
  int nfaces = 0;
  int bytesPerPixel = 0;
  int redL = 0, redR = 0;
  int greenL = 0, greenR = 0;
  int blueL = 0, blueR = 0;
  int alphaL = 0, alphaR = 0;
};

inline void calc_shifts(int mask, int& left, int& right) {
  if (mask == 0) {
    left = right = 0;
    return;
  }

  int i, tmp = mask;
  for (i = 0; i < 32; i++, tmp >>= 1) {
    if (tmp & 1) break;
  }
  right = i;

  for (i = 0; i < 8; i++, tmp >>= 1) {
    if (!(tmp & 1)) break;
  }
  left = 8 - i;
}

bool internal_readimg(Stream* stream, uint8_t* dst, int w, int h, int d,
                      const DdsDecodeState& state) {
  if (state.dds.fmt.flags & DDS_PF_FOURCC) {
    // compressed image
    int flags = 0;
    switch (state.dds.fmt.fourCC) {
      case DDS_4CC_DXT1:
        flags = squish::kDxt1;
        break;
      // DXT2 and 3 are the same, only 2 has pre-multiplied alpha
      case DDS_4CC_DXT2:
      case DDS_4CC_DXT3:
        flags = squish::kDxt3;
        break;
      // DXT4 and 5 are the same, only 4 has pre-multiplied alpha
      case DDS_4CC_DXT4:
      case DDS_4CC_DXT5:
        flags = squish::kDxt5;
        break;
    }
    // create source buffer
    std::vector<squish::u8> tmp(squish::GetStorageRequirements(w, h, flags));
    // load image into buffer
    if (tmp.empty() ||
        stream->Read(tmp.data(), static_cast<int64_t>(tmp.size())) !=
            static_cast<int64_t>(tmp.size()))
      return false;
    // decompress image
    squish::DecompressImage(dst, w, h, &tmp[0], flags);
    tmp.clear();
    // correct pre-multiplied alpha, if necessary
    if (state.dds.fmt.fourCC == DDS_4CC_DXT2 || state.dds.fmt.fourCC == DDS_4CC_DXT4) {
      int k;
      for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
          k = (y * w + x) * 4;
          if (dst[k + 3] == 0) {
            dst[k + 0] = dst[k + 1] = dst[k + 2] = 0;
            continue;
          }
          dst[k + 0] = (uint8_t)((int)dst[k + 0] * 255 / (int)dst[k + 3]);
          dst[k + 1] = (uint8_t)((int)dst[k + 1] * 255 / (int)dst[k + 3]);
          dst[k + 2] = (uint8_t)((int)dst[k + 2] * 255 / (int)dst[k + 3]);
        }
      }
    }
  } else {
    // uncompressed image

    // HACK: shortcut for luminance
    if (state.dds.fmt.flags & DDS_PF_LUMINANCE) {
      return stream->Read(dst, w * state.bytesPerPixel * h);
    }

    int k, pixel = 0;
    for (int z = 0; z < d; z++) {
      for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
          if (!stream->Read(&pixel, state.bytesPerPixel)) return false;
          k = (z * h * w + y * w + x) * state.nchans;
          dst[k + 0] =
              (uint8_t)(((pixel & state.dds.fmt.rmask) >> state.redR) << state.redL);
          dst[k + 1] =
              (uint8_t)(((pixel & state.dds.fmt.gmask) >> state.greenR) << state.greenL);
          dst[k + 2] =
              (uint8_t)(((pixel & state.dds.fmt.bmask) >> state.blueR) << state.blueL);
          if (state.dds.fmt.flags & DDS_PF_ALPHA)
            dst[k + 3] =
                (uint8_t)(((pixel & state.dds.fmt.amask) >> state.alphaR) << state.alphaL);
        }
      }
    }
  }
  return true;
}

bool TextureLoadDDS(Stream* stream, Texture* outTexture) {
  DdsDecodeState state{};
  stream->Seek(0, IoSeek::Set);

  state.dds.fourCC = ReadLE<uint32_t>(stream);
  state.dds.size = ReadLE<uint32_t>(stream);
  state.dds.flags = ReadLE<uint32_t>(stream);
  state.dds.height = ReadLE<uint32_t>(stream);
  state.dds.width = ReadLE<uint32_t>(stream);
  state.dds.pitch = ReadLE<uint32_t>(stream);
  state.dds.depth = ReadLE<uint32_t>(stream);
  state.dds.mipmaps = ReadLE<uint32_t>(stream);

  // advance the file pointer by 44 bytes (reserved fields)
  stream->Seek(44, IoSeek::Cur);

  // pixel format struct
  state.dds.fmt.size = ReadLE<uint32_t>(stream);
  state.dds.fmt.flags = ReadLE<uint32_t>(stream);
  state.dds.fmt.fourCC = ReadLE<uint32_t>(stream);
  state.dds.fmt.bpp = ReadLE<uint32_t>(stream);
  state.dds.fmt.rmask = ReadLE<uint32_t>(stream);
  state.dds.fmt.gmask = ReadLE<uint32_t>(stream);
  state.dds.fmt.bmask = ReadLE<uint32_t>(stream);
  state.dds.fmt.amask = ReadLE<uint32_t>(stream);

  // caps
  state.dds.caps.flags1 = ReadLE<uint32_t>(stream);
  state.dds.caps.flags2 = ReadLE<uint32_t>(stream);

  // advance the file pointer by 12 bytes (reserved fields)
  stream->Seek(12, IoSeek::Cur);

  // sanity checks - valid 4CC, correct struct sizes and flags which should
  // be always present, regardless of the image type, size etc., also check
  // for impossible flag combinations
  if (state.dds.fourCC != DDS_MAKE4CC('D', 'D', 'S', ' ') || state.dds.size != 124 ||
      state.dds.fmt.size != 32 || !(state.dds.caps.flags1 & DDS_CAPS1_TEXTURE) ||
      !(state.dds.flags & DDS_CAPS) || !(state.dds.flags & DDS_PIXELFORMAT) ||
      (state.dds.caps.flags2 & DDS_CAPS2_VOLUME &&
       !(state.dds.caps.flags1 & DDS_CAPS1_COMPLEX && state.dds.flags & DDS_DEPTH)) ||
      (state.dds.caps.flags2 & DDS_CAPS2_CUBEMAP &&
       !(state.dds.caps.flags1 & DDS_CAPS1_COMPLEX))) {
    stream->Seek(0, IoSeek::Set);
    return false;
  }

  // make sure all dimensions are > 0 and that we have at least one channel
  // (for uncompressed images)
  if (!(state.dds.flags & DDS_WIDTH) || !state.dds.width ||
      !(state.dds.flags & DDS_HEIGHT) || !state.dds.height ||
      ((state.dds.flags & DDS_DEPTH) && !state.dds.depth) ||
      (!(state.dds.fmt.flags & DDS_PF_FOURCC) &&
       !((state.dds.fmt.flags & DDS_PF_RGB) | (state.dds.fmt.flags & DDS_PF_LUMINANCE) |
         (state.dds.fmt.flags & DDS_PF_ALPHA)))) {
    stream->Seek(0, IoSeek::Set);
    return false;
  }

  // validate the pixel format
  // TODO: support DXGI and the "wackier" uncompressed formats
  if (state.dds.fmt.flags & DDS_PF_FOURCC && state.dds.fmt.fourCC != DDS_4CC_DXT1 &&
      state.dds.fmt.fourCC != DDS_4CC_DXT2 && state.dds.fmt.fourCC != DDS_4CC_DXT3 &&
      state.dds.fmt.fourCC != DDS_4CC_DXT4 && state.dds.fmt.fourCC != DDS_4CC_DXT5) {
    stream->Seek(0, IoSeek::Set);
    return false;
  }

  // determine the number of channels we have
  if (state.dds.fmt.flags & DDS_PF_FOURCC) {
    // squish decompresses everything to RGBA anyway
    state.nchans = 4;
  } else {
    state.nchans = ((state.dds.fmt.flags & DDS_PF_LUMINANCE) ? 1 : 3) +
               ((state.dds.fmt.flags & DDS_PF_ALPHA) ? 1 : 0);
    // also calculate bytes per pixel and the bit shifts
    state.bytesPerPixel = (state.dds.fmt.bpp + 7) >> 3;
    if (!(state.dds.fmt.flags & DDS_PF_LUMINANCE)) {
      calc_shifts(state.dds.fmt.rmask, state.redL, state.redR);
      calc_shifts(state.dds.fmt.gmask, state.greenL, state.greenR);
      calc_shifts(state.dds.fmt.bmask, state.blueL, state.blueR);
      calc_shifts(state.dds.fmt.amask, state.alphaL, state.alphaR);
    }
  }

  // fix depth, pitch and mipmaps for later use, if needed
  if (!(state.dds.fmt.flags & DDS_PF_FOURCC && state.dds.flags & DDS_PITCH))
    state.dds.pitch = state.dds.width * state.bytesPerPixel;
  if (!(state.dds.caps.flags2 & DDS_CAPS2_VOLUME)) state.dds.depth = 1;
  if (!(state.dds.flags & DDS_MIPMAPCOUNT)) state.dds.mipmaps = 1;
  // count cube map faces
  if (state.dds.caps.flags2 & DDS_CAPS2_CUBEMAP) {
    state.nfaces = 0;
    for (int flag = DDS_CAPS2_CUBEMAP_POSITIVEX;
         flag <= DDS_CAPS2_CUBEMAP_NEGATIVEZ; flag <<= 1) {
      if (state.dds.caps.flags2 & flag) state.nfaces++;
    }
  } else
    state.nfaces = 1;

  TexFmt texFmt = TexFmt_RGBA;
  if (state.nchans == 3) {
    texFmt = TexFmt_RGB;
  } else if (state.nchans != 4) {
    texFmt = TexFmt_U8;
  }

  outTexture->Init(texFmt, state.dds.width, state.dds.height);
  return internal_readimg(stream, outTexture->Buffer.data(), state.dds.width,
                          state.dds.height, state.dds.depth, state);
}

static bool _registered = Texture::AddTextureLoader(&TextureLoadDDS);

}  // namespace Gxm
}  // namespace Impacto
