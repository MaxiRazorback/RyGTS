# On-demand Native staging rings

Apply `shadGT-patches/0081-native-on-demand-staging-rings.patch` after the existing renderer patches through 0072. Other category patches are independent.

Native mode no longer eagerly constructs the legacy upload ring and two stage rings it normally does not use. Each retains its original capacity, memory type and ownership, and is initialized on first demand with std::call_once. Failed construction can retry. Additional worker rings retain their half-size policy. The tiler holds BufferCache rather than forcing the stream ring during construction. Other renderer modes retain eager initialization.

The diagnostic identity pointer is published atomically after construction. No required read is redirected to disk and no backing is evicted. Local comparison toggles and allocation logs are excluded.

Validation: the original Release candidate passed 2,610 local import checks and the Vulkan image self-test. Two track/menu cycles had correct performance; an intermittent showroom color defect was captured and attribution remains unresolved. None of the three rings allocated during those cycles. Avoided eager capacity is 384 MiB on the tested GPU; this is not a measured reduction in whole-process peak commit or proof of 8-GB support. The extracted patch also passes standalone application and affected translation-unit syntax checks.
