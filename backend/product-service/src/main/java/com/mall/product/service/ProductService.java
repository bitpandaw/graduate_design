package com.mall.product.service;

import com.mall.product.Product;
import com.mall.product.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    public List<Product> getAllProducts() {
        return productRepository.findAll();
    }

    public Optional<Product> getProductById(Long id) {
        return productRepository.findById(id);
    }

    public List<Product> getProductsByCategory(Product.Category category) {
        return productRepository.findByCategory(category);
    }

    public List<Product> searchProducts(String keyword) {
        return productRepository.findByNameContaining(keyword);
    }

    public List<Product> getProductsByIds(List<Long> ids) {
        return productRepository.findByIdIn(ids);
    }

    public Product createProduct(Product product) {
        return productRepository.save(product);
    }

    public Optional<Product> updateProduct(Long id, Product updatedProduct) {
        return productRepository.findById(id).map(product -> {
            product.setName(updatedProduct.getName());
            product.setPrice(updatedProduct.getPrice());
            product.setStock(updatedProduct.getStock());
            product.setCategory(updatedProduct.getCategory());
            product.setDescription(updatedProduct.getDescription());
            return productRepository.save(product);
        });
    }

    public void deleteProduct(Long id) {
        productRepository.deleteById(id);
    }
}
