package com.mall.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class MallGatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(MallGatewayApplication.class, args);
    }

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("user_service", r -> r.path("/api/users/**")
                .uri("http://localhost:8081"))
            .route("product_service", r -> r.path("/api/products/**")
                .uri("http://localhost:8082"))
            .route("order_service", r -> r.path("/api/orders/**")
                .uri("http://localhost:8083"))
            .route("recommendation_service", r -> r.path("/api/recommendations/**")
                .uri("http://localhost:8084"))
            .route("search_service", r -> r.path("/api/search/**")
                .uri("http://localhost:8085"))
            .route("payment_service", r -> r.path("/api/payments/**")
                .uri("http://localhost:8086"))
            .build();
    }
}