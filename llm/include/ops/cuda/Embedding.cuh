#include <cassert>
#include "common.h"

class Embedding_cuda {
   public:
    Embedding_cuda(int embed_dim_, int voc_size_, int padding_idx_, Matrix3D<float> lookup_)
        : embed_dim(embed_dim_), voc_size(voc_size_), padding_idx(padding_idx_), lookup(lookup_) {
            assert(lookup_.m_dim_y == voc_size_);
            assert(lookup_.m_dim_z == embed_dim_);
        }
    Embedding_cuda(){};
    void forward(Matrix3D<int> input_id, Matrix3D<half> output);
    int embed_dim, voc_size, padding_idx;
    Matrix3D<float> lookup;
private:
    std::string profile_name = "Embedding";
};

void load_Embedding_params_cuda(Embedding_cuda &op, std::string prefix);
