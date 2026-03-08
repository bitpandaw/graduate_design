package com.mall.payment.service;

import com.mall.payment.model.Payment;
import com.mall.payment.repository.PaymentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class PaymentService {

    private final PaymentRepository paymentRepository;

    public Payment createPayment(Payment payment) {
        payment.setStatus(Payment.PaymentStatus.PENDING);
        payment.setTransactionId(UUID.randomUUID().toString());
        payment.setCreatedAt(LocalDateTime.now());
        payment.setUpdatedAt(LocalDateTime.now());
        return paymentRepository.save(payment);
    }

    public Optional<Payment> getPaymentById(Long id) {
        return paymentRepository.findById(id);
    }

    public Optional<Payment> getPaymentByOrderId(Long orderId) {
        return paymentRepository.findByOrderId(orderId);
    }

    public List<Payment> getPaymentsByUserId(Long userId) {
        return paymentRepository.findByUserId(userId);
    }

    /**
     * 模拟支付完成
     */
    public Optional<Payment> completePayment(Long id) {
        return paymentRepository.findById(id).map(payment -> {
            payment.setStatus(Payment.PaymentStatus.SUCCESS);
            payment.setUpdatedAt(LocalDateTime.now());
            return paymentRepository.save(payment);
        });
    }

    /**
     * 模拟退款
     */
    public Optional<Payment> refundPayment(Long id) {
        return paymentRepository.findById(id).map(payment -> {
            payment.setStatus(Payment.PaymentStatus.REFUNDED);
            payment.setUpdatedAt(LocalDateTime.now());
            return paymentRepository.save(payment);
        });
    }
}
