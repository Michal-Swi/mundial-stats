#include "elo_parser.hpp"

int main() {
	EloParser ep;
	auto db = ep.parse();

	for (int i = 0; i < db["CZ"].size(); i++) {
		std::cout << db["CZ"][i].year << ' ';
		std::cout << db["CZ"][i].month << ' ';
		std::cout << db["CZ"][i].day << ' ';
		std::cout << db["CZ"][i].opponent_code << ' ';
		std::cout << db["CZ"][i].elo << ' ';
		std::cout << std::endl;
	}

	return 0;
}

