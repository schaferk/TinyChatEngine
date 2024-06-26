#include <cstring>

#include "operators.h"
#include "utils.h"

__global__ void EmbeddingKernel(Matrix3D<int> input_id, Matrix3D<half> output, float* lookup, int embed_dim) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < input_id.m_dim_z) {
        int token_id = input_id(0, 0, i);
        half* output_sample_ptr = &output.m_data[i * embed_dim];
        float* target_embed = &lookup[token_id * embed_dim];

        for (int j = 0; j < embed_dim; ++j) {
            output_sample_ptr[j] = __float2half(target_embed[j]);
        }
    }
}

void load_Embedding_params_cuda(Embedding_cuda& op, std::string prefix) {
    op.lookup.load((prefix + "/weight.bin").c_str());
}

void Embedding_cuda::forward(Matrix3D<int> input_id, Matrix3D<half> output) {
    PROFILE_START(profile_name);
    assert(input_id.m_dim_x == 1);
    assert(input_id.m_dim_y == 1);
    assert(input_id.m_dim_z == output.m_dim_y);
    assert(output.m_dim_z == this->embed_dim);

    int threadsPerBlock = 1024;
    int blocksPerGrid = (input_id.m_dim_z + threadsPerBlock - 1) / threadsPerBlock;
    EmbeddingKernel<<<blocksPerGrid, threadsPerBlock>>>(input_id, output, this->lookup.m_data, this->embed_dim);

    PROFILE_END(profile_name);
}
