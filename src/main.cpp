#include "elo_parser.hpp"

int main() {
	EloParser ep; 
	ep.dump_dixon_coles_data(ep.parse_dixon_coles("../data/dixon-coles-2023"), 
											      "../data/model/dixon-coles");

	return 0;
}

