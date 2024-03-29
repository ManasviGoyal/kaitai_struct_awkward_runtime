.PHONY: list test all clean

# Remove --debug to strip debugging symbols from the library
BUILD = local/bin/awkward-kaitai-build --debug
JAVA_CLASSES = kaitai_struct_compiler/jvm/target/scala-2.12/classes/io/kaitai/struct

# This path only works on Linux, need to make it compatible with WSL as well
JAR_PATH = /usr/share/kaitai-struct-compiler/lib/*

KSY := animal fake index_option numpy pixie4e records scdms hello_world scdms_v8 simple_enum

LIBS := $(foreach ksy,$(KSY),test_artifacts/lib$(ksy).so)

compile_test: # define testcase environment variable
	rm -f test_artifacts/lib$(testcase).so
	PYTHONPATH=$$PYTHONPATH:local $(BUILD) test_artifacts/$(testcase).cpp -b build
	pytest tests/test_$(testcase).py

cpp: $(foreach ksy,$(KSY),test_artifacts/$(ksy).cpp)

test_artifacts/lib%.so: test_artifacts/%.cpp $(BUILD)
	PYTHONPATH=$$PYTHONPATH:local $(BUILD) $< -b build

$(BUILD): kaitai_struct_compiler/shared/src/main/scala/io/kaitai/struct/languages/AwkwardCompiler.scala
	pip install . -t local

test_artifacts/%.cpp: example_data/schemas/%.ksy $(JAVA_CLASSES)
	java -cp kaitai_struct_compiler/jvm/target/scala-2.12/kaitai-struct-compiler_2.12-0.11-SNAPSHOT.jar:$(JAR_PATH) io.kaitai.struct.JavaMain -t awkward --outdir test_artifacts $<

$(JAVA_CLASSES): kaitai_struct_compiler/shared/src/main/scala/io/kaitai/struct/languages/AwkwardCompiler.scala
	cd kaitai_struct_compiler && sbt package

test: $(LIBS)
	pytest

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

clean:
	rm -rf local test_artifacts && cd kaitai_struct_compiler && rm -fr js/target/ jvm/target/ project/project/ project/target/ target/ .bsp/
