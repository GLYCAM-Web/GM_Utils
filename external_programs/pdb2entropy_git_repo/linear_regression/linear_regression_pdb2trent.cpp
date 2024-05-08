#include<iostream>
#include<string>
#include<vector>
#include<cmath>
#include<fstream>

//command line: ./linear_regression.exe moiety_name pdb2entropy_output_file
int main(int argc, char* argv[]){
	if (argc < 4){
		std::cout << "Usage: ./linear_regression.exe moiety_name pdb2entropy_output_file result_output_file" << std::endl;
		std::exit(1);
	}

	std::string moiety_name(argv[1]);
	std::string pdb2entropy_output(argv[2]);
	std::ifstream output(pdb2entropy_output);
	if (output.fail()){
		std::cout << "Failed to open " << pdb2entropy_output << " for reading." << std::endl;
		std::exit(1);
	}

	std::vector<std::string> percentages_line;
	std::vector<std::string> results_line;
	std::string line;
	std::string keyword_1 = "Begin Entropy Calculation using the first ";
	std::string keyword_2 = "% of the entire trajectory";
	std::string keyword_3 = "Trans/Rot entropy estimate on weighted linear regression";

	while (std::getline(output, line)){
		if (line.find(keyword_1) != std::string::npos){
			percentages_line.push_back(line);
		}
		else if(line.find(keyword_3) != std::string::npos){
			std::getline(output, line);
			results_line.push_back(line);
		}
	}
	output.close();
	
	if (percentages_line.size() != results_line.size()){
		std::cout << "Error, number of x values " << percentages_line.size() << " does not equal the number of y values " << results_line.size() << std::endl;
		std::exit(1);
	}

	std::vector<double> xs;
	std::vector<double> ys;

	double avg_x = 0, avg_y = 0;
	for (unsigned int i = 0; i < percentages_line.size(); i++){
		std::string sx = percentages_line[i];
		sx.erase(sx.find(keyword_1), keyword_1.length());
		sx.erase(sx.find(keyword_2), keyword_2.length());
		double percentage = std::stod(sx);
		double x = 100 / percentage;

 		std::string sy = results_line[i];
        std::string entropy_str = sy.substr(0, sy.find("+/-"));
        //std::cout << "Entropy str: " << entropy_str << std::endl;
        double entropy = std::stod(entropy_str) * 0.001987; //R unit in kcal/mol
        double y = 1 / entropy;

		if(std::isnan(x) || std::isnan(y)){
            std::cout << "Skipping NaN data point (" << 1/x << " , " << y << ")." << std::endl;
			if (std::isnan(y)){
				std::cout << "Y = Nan is probably due to using too few frames for pdb2trent. Consider repeating with more frames in the trajectory." << std::endl;
			}
			if (std::isnan(x)){
				std::cout << "Since X = Nan, please talk to Yao immediately. There must be something wrong with the scripts/programs." << std::endl;
			}
            continue;
        }

		xs.push_back(x); // 1 over percentages. For example, 100 over 10(%) = 10. 
		ys.push_back(y);
		avg_x += x;
		avg_y += y;
	}

	avg_x /= xs.size();
	avg_y /= ys.size();
	
	double slope_xy = 0, slope_xx = 0;
	for (unsigned int i = 0; i < xs.size(); i++){
		double& x = xs[i];
		double& y = ys[i];
		slope_xy += (x-avg_x)*(y-avg_y);
		slope_xx += (x-avg_x)*(x-avg_x);
	}
	double slope = slope_xy / slope_xx;
	double y_intercept = avg_y - slope * avg_x;

	double r2_yi = 0, r2_y_bar = 0;
	for (unsigned int i = 0; i < xs.size(); i++){
		double& x = xs[i];
        double& y = ys[i];
		double y_predicted =  slope * x + y_intercept;
		r2_yi += (y-y_predicted)*(y-y_predicted);
		r2_y_bar += (y-avg_y) * (y-avg_y);
	}
	double r2 = 1 - r2_yi / r2_y_bar;

	double entropy_interpolated = 1 / y_intercept * (-300);
	std::cout << moiety_name << " " << entropy_interpolated << " " << y_intercept << " " << slope << " " << r2 << std::endl;

	std::string outputfile_path(argv[3]);
	std::ofstream linear_regression(outputfile_path);
	if (linear_regression.fail()){
		std::cout << "Failed to open " << outputfile_path << " for writing." << std::endl;
		std::exit(1);
	}
	linear_regression << moiety_name << " " << entropy_interpolated << " " << y_intercept << " " << slope << " " << r2 << std::endl;
	linear_regression.close();
	return 0;
}
