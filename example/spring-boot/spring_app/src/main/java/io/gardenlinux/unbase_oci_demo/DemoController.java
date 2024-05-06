package io.gardenlinux.unbase_oci_demo;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.GetMapping;

@RestController
public class DemoController {

    @GetMapping("/")
    String foo() {
        return "Hello World";
    }
}
