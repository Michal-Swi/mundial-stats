#include "elo_parser.hpp"

int main() {
	EloParser ep; 
	ep.parse();
	ep.dump_data("../data/training_data/data.csv");

	return 0;
}

