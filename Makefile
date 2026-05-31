SAMPLES_DIR := tests/samples
SAMPLE_FILE_1 := $(SAMPLES_DIR)/file1.wav
SAMPLE_FILE_ERROR := $(SAMPLES_DIR)/file1-error.wav
SAMPLE_FILE_2 := $(SAMPLES_DIR)/file2.wav

.DEFAULT_GOAL := help

.PHONY: help samples clean

help: ## Show this help
	@grep -E '^[a-z][a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk -F ':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

samples: $(SAMPLE_FILE_1) $(SAMPLE_FILE_ERROR) $(SAMPLE_FILE_2) ## Generate sample WAV fixtures

$(SAMPLE_FILE_1): | $(SAMPLES_DIR)
	ffmpeg -y -hide_banner -loglevel error \
		-f lavfi -i 'sine=frequency=180:duration=5:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=250:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=330:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=470:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=610:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=730:duration=2:sample_rate=16000' \
		-filter_complex '[0:a][1:a][2:a][3:a][4:a][5:a]concat=n=6:v=0:a=1[out]' \
		-map '[out]' $@

$(SAMPLE_FILE_ERROR): | $(SAMPLES_DIR)
	ffmpeg -y -hide_banner -loglevel error \
		-f lavfi -i 'sine=frequency=145:duration=4:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=205:duration=4:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=285:duration=4:sample_rate=16000' \
		-filter_complex '[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]' \
		-map '[out]' $@

$(SAMPLE_FILE_2): | $(SAMPLES_DIR)
	ffmpeg -y -hide_banner -loglevel error \
		-f lavfi -i 'sine=frequency=250:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=330:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=470:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=610:duration=2:sample_rate=16000' \
		-f lavfi -i 'sine=frequency=730:duration=2:sample_rate=16000' \
		-filter_complex '[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[out]' \
		-map '[out]' $@

$(SAMPLES_DIR):
	mkdir -p $(SAMPLES_DIR)

clean: ## Remove generated sample WAV fixtures
	rm -f $(SAMPLE_FILE_1) $(SAMPLE_FILE_ERROR) $(SAMPLE_FILE_2)
