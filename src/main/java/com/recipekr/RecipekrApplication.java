package com.recipekr;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
public class RecipekrApplication {

    public static void main(String[] args) {
        SpringApplication.run(RecipekrApplication.class, args);
    }
}
