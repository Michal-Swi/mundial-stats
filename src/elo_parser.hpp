#include <string>
#include <chrono>
#include <sstream>
#include <utility>
#include <vector>
#include <fstream>
#include <iostream>
#include <map>

/* THE PLAN 
 * 1. Seperate the timelines, the main timeline should 
 * contain EVERY single match and calculate variables from 
 * there. 
 * 2. The second timeline is the stat model timeline, no 
 * "Friendly" matches. */ 

struct Elo {
	int year;
	int month; 
	int day;
	std::string opponent_code;
	int elo;
	int days_passed; 
	bool friendly;
};

// string is the country code 
using db = std::map<std::string, std::vector<Elo>>;

class EloParser {
	private:
	db historical_elo_records;
	db model_elo_records;

	// translates country name to country code
	public:
	std::map<std::string, std::string> translator; 
	std::vector<std::string> world_cup_countries; 

	private:
	std::vector<std::string> get_all_countries() {
		std::ifstream countries_file("../data/tsv_names.csv");
		std::vector<std::string> all_countries;

		std::string country;
		while (countries_file >> country) {
			all_countries.push_back(country);
		}

		return all_countries;
	}

	public:
	void parse_codes() {
        std::ifstream countries_file("../data/en.teams.tsv");

        std::string line;
        while (std::getline(countries_file, line)) {
            std::stringstream ss(line);
            std::string code, name;

            if (std::getline(ss, code, '\t')) {
                std::getline(ss, name, '\t');
                translator[code] = name;
            }
        }	
	}

	public:
	void parse_world_cup_countries() {
		const std::string path = 
			"../data/current_countries.csv";
		std::ifstream world_cup_countries_file(path);
		
		std::string line; 
		while (std::getline(world_cup_countries_file, line)) {
			world_cup_countries.push_back(line);
		}
	}

	private:
	void parse_country(const std::string &path, const std::string &country_name) {
		std::ifstream country_file(path);
		std::string line;

		while (std::getline(country_file, line)) {
			std::stringstream ss(line);
			std::string token;
			std::vector<std::string> cols;

			while (std::getline(ss, token, '\t')) {
				cols.push_back(token);
			}

			int year = std::stoi(cols.at(0));
			int month = std::stoi(cols.at(1));
			int day = std::stoi(cols.at(2));

			if (year < 2023) {
				continue;
			}

			std::string us = cols.at(3);
			std::string enemy = cols.at(4);

			int us_goals = std::stoi(cols.at(5));
			int enemy_goals = std::stoi(cols.at(6));

			int us_elo = std::stoi(cols.at(10)) - std::stoi(cols.at(9));
			int enemy_elo = std::stoi(cols.at(11)) + std::stoi(cols.at(9));
			
			if (translator[us] != country_name) {
				std::swap(us, enemy);
				std::swap(us_goals, enemy_goals);
				std::swap(us_elo, enemy_elo);
			}

			Elo elo; 

			if (cols.at(7) == "F") {
				elo.friendly = true;
			} else {
				elo.friendly = false;
			}

			elo.elo = us_elo;
			elo.year = year;
			elo.month = month;
			elo.day = day;
			elo.opponent_code = enemy;
			historical_elo_records[us].push_back(elo);
		}
	}

	private:
	std::string delete_extension(const std::string &s) {
		std::string n_s = "";
		for (const auto &ch : s) {
			if (ch == '.') {
				break;
			} else if (ch == '_') {
				n_s += ' ';
				continue;
			}

			n_s += ch; 
		}

		return n_s;
	}
	
	private:
	void fill_model_db(const std::string &cc, const std::vector<Elo> &historical_data) {
		// the i = 0 has no known previous match date; we have to skip it

		auto prev = historical_data.at(0);
		for (int i = 1; i < historical_data.size(); i++) {
			auto record = historical_data.at(i);
			auto date_post = (std::chrono::year(record.year)/
						      std::chrono::month(record.month)/
							  std::chrono::day(record.day));
			auto date_prev = (std::chrono::year(prev.year)/
					          std::chrono::month(prev.month)/
							  std::chrono::day(prev.day));
			auto datediff = static_cast<std::chrono::sys_days>(date_post) 
						  - static_cast<std::chrono::sys_days>(date_prev);

			record.days_passed = static_cast<unsigned>(datediff.count());

			// Capping at 10
			if (record.days_passed > 10) {
				record.days_passed = 10;
			}

			if (!record.friendly) {
				model_elo_records[cc].push_back(record);
			}

			prev = record;
		}
	}

	public:
	db parse() {
		parse_world_cup_countries();
		parse_codes(); // country code translation

		// These are only the initial parses - 1. from the plan
		const std::string path = "../data/elo/";
		for (const auto &country : get_all_countries()) {
			std::string curr_path = path + country;
			parse_country(curr_path, delete_extension(country));
		}

		for (const auto &[cc, data_arr] : historical_elo_records) {
			fill_model_db(cc, data_arr);
		}

		return model_elo_records;
	}
};

