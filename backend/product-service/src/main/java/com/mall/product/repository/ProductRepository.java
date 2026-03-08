package com.mall.product.repository;

import com.mall.product.Product;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ProductRepository extends JpaRepository<Product, Long> {

    List<Product> findByCategory(Product.Category category);

    List<Product> findByNameContaining(String keyword);

    List<Product> findByIdIn(List<Long> ids);
}
