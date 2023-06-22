# install.packages('ggplot2')
# install.packages("dplyr")
# install.packages("tibble")
# install.packages("ggpmisc")


library(ggplot2)
library(dplyr)
library(tibble)
library(ggpmisc)

################################ general functions 

addVectorToList <- function (lst,v){
  lst <- c(lst, list(v))
  return(lst)
}
##################################  configurations:

origin_path <- "/workingDir"
setwd(origin_path)
getwd()    
v_count_100 <- 25470
v_count_75 <- 18825
path_exp1 <- "/data/Experiment1-realistic-high-load"
path_exp2 <- "/data/Experiment2-rand-high-load"
path_exp3 <- "/data/Experiment3-realistic-moderate-load"
path_exp4 <- "/data/Experiment4-and-moderate-load"

colors <- c("Tree 20 runs" = "#2f99d6", "Trunk 20 runs" = "#c9061d", "SUMO Actuated 20 runs" = "#a832a8")

################################# Bars with errors - Figures 3 and 4:

add_measurment_vector <- function(data, index, col_names, datalist, run_type) {
  for (i in col_names) {
    dat <- data.frame(method_name = i,
                      n_mean = mean(data[[i]]),
                      se = sd(data[[i]]) / sqrt(length(data[[i]])),
                      run_type = run_type)
    datalist[[index]] <- dat
    index <- index + 1
  }
  return (datalist)
}

print_col_with_e_bars <- function(df, experiment, title, y_title, x_title, first_series, second_series, feagure_id) {
  df$method_name <- factor(df$method_name, levels = c('Tree', 'Actuated', 'Uniform', 'Random Phase'))
  df$run_type <- factor(df$run_type, levels = c(second_series, first_series))
  p <- ggplot(df, aes(x = n_mean, y = method_name, color, fill = run_type), linewidth = 0.2) + 
    geom_bar(stat = "identity", color = "black", position = "dodge") +
    geom_errorbar(aes(xmin = n_mean - se, xmax = n_mean + se), width = .2,
                  position = position_dodge(width = .9))+ 
    labs(title = title, x = x_title, y = y_title)+
    theme_classic() +
    theme(plot.title = element_text(hjust = 0.5), 
          axis.title.x = element_text(size = 12),
          axis.title.y = element_text(size = 12),
          legend.title = element_blank(),
          axis.text = element_text(size = 10)) + 
    scale_fill_manual(values = c("#c23838", "#f9c74f"), breaks = c(first_series, second_series))
  fileName <- sprintf("%s-%s-%s.pdf",feagure_id, experiment, title)
  pdf(fileName)
  print(p)
  dev.off()
}

print_mean_cols <- function (data_100, data_75, experiment, run_type_100, run_type_75, measure, units, feagure_id) {
  col_names <- colnames(data_100)
  datalist <- vector("list", length = length(col_names) * 2)
  index <- 1
  datalist <- add_measurment_vector(data_75, index, col_names, datalist, run_type_75)

  index <- length(col_names) + 1
  datalist <- add_measurment_vector(data_100, index, col_names, datalist, run_type_100)
  data_with_se <- do.call(rbind, datalist)
  setwd(origin_path)
  print_col_with_e_bars(data_with_se, experiment,
                        sprintf("%s per Traffic Light Method",measure),
                        "Traffic Light Method", sprintf("%s %s", measure, units),run_type_100, run_type_75, feagure_id)
}

get_analysis_from_output <- function(path, file_name) {
  setwd(path)
  df <- read.delim(file_name, sep = ",")
  df <- data.frame(df$Uniform , df$Random , df$Actuated , df$CurrentTree)
  names(df) <- c('Uniform', 'Random Phase', 'Actuated', 'Tree')
  return (df)
}

driving_time_file_name <- "res_time per v.txt"
arriving_file_name <- "res_ended_vehicles_count.txt"

data_100 <- get_analysis_from_output(path_exp1, driving_time_file_name)
data_75 <- get_analysis_from_output(path_exp3, driving_time_file_name)
print_mean_cols(data_100, data_75, 'realistic', 'High Load', 'Moderate Load', 'Average Driving Time', '[S]', '4A')

data_100 <- get_analysis_from_output(path_exp2, driving_time_file_name)
data_75 <- get_analysis_from_output(path_exp4, driving_time_file_name)
print_mean_cols(data_100, data_75, 'rand', 'High Load', 'Moderate Load', 'Average Driving Time', '[S]', '3A')

data_100 <- get_analysis_from_output(path_exp1, arriving_file_name)
data_75 <- get_analysis_from_output(path_exp3, arriving_file_name)
print_mean_cols(data_100 / v_count_100, data_75 / v_count_75, 'realistic', 'High Load', 'Moderate Load', 'Throughput Ratio', '', '4B')

data_100 <- get_analysis_from_output(path_exp2, arriving_file_name)
data_75 <- get_analysis_from_output(path_exp4, arriving_file_name)
print_mean_cols(data_100 / v_count_100, data_75 / v_count_75, 'rand', 'High Load', 'Moderate Load', 'Throughput Ratio', '', '3B')


################################# Probability: Figure 5 #####

get_checkpoint_values <- function(ecdf){
  this_ecdf <- ggplot() + ecdf
  ecdf.data <- layer_data(this_ecdf)
  ecdf.df <- data.frame(ecdf.data$x, ecdf.data$y)
  ecdf.df <- ecdf.df[order(ecdf.df$ecdf.data.y),]
  ecdf.df$ecdf.data.x[1] <- 0
  res <- NULL
  x_checkpoint <- 1
  for (j in 1:(length(ecdf.data$x) - 2)) {
    if (ecdf.df$ecdf.data.x[j] <= x_checkpoint * 100) {
      res[x_checkpoint] <- ecdf.df$ecdf.data.y[j]
    } else {
      for (p in x_checkpoint:(ecdf.df$ecdf.data.x[j]/100)){
        x_checkpoint <- x_checkpoint + 1
        res[x_checkpoint] <- ecdf.df$ecdf.data.y[j]
      }
    }
  }
  res <- c(res, 1)
  return (res)
}

get_checkpoint_avg <- function(checkpoint_list, max_checkpoint_size) {
  for (i in 1:length(checkpoint_list)) {
    vec <- unlist(checkpoint_list[i])
    unified_vec <- c(vec, rep(1, max_checkpoint_size - length(vec)))
    if(i == 1) {
      df <- data.frame(unified_vec)
    } else {
      df <- cbind(df, data.frame(unified_vec))
    }
  }
  mean <- rowMeans(df)
  return (mean)
}
  
add_ecdf_to_figure <- function(figure, directory_path, N, tl_method, color, col_index, file_name) {
  method_df <- data.frame()
  checkpoint_values <- list();
  max_checkpoint_size <- 0
  for (i in 1:N) {
    path <- sprintf("%s/%s/%s", directory_path, i, tl_method)
    setwd(path)
    data <- read.delim(file_name, sep = ",")
    df <- data.frame(data[col_index])
    names(df)[1] <- "v"

    ecdf <-stat_ecdf(geom = "step", data = df, aes(v, color = color), linewidth = 0.2)
    figure <- figure + ecdf
    
    res <- get_checkpoint_values(ecdf)
    max_checkpoint_size <- max(max_checkpoint_size, length(res))
    checkpoint_values <- addVectorToList(checkpoint_values, res)
  }
  checkpoint_avg <- get_checkpoint_avg(checkpoint_values, max_checkpoint_size)
  result <- list("figure" = figure, "checkpoint_avg" = checkpoint_avg)
  return (result)
}

print_ecdf_figure <- function(path, title, x_title, y_title, N, series, col_index, file_name, colors, feagure_id) {
  density <- ggplot()
  if ("CurrentTrunk" %in% series) {
    res <- add_ecdf_to_figure(density, path, N, "CurrentTrunk","Trunk 20 runs", col_index, file_name)
    density <- res$figure
  }
  if ("CurrentTreeDvd" %in% series) {
    res <- add_ecdf_to_figure(density, path, N, "CurrentTreeDvd", "Tree 20 runs", col_index, file_name)
    density <- res$figure
    checkpoints_a <- res$checkpoint_avg
  }
  if ("SUMOActuated" %in% series) {
    res <- add_ecdf_to_figure(density, path, N, "SUMOActuated", "SUMO Actuated 20 runs", col_index, file_name)
    density <- res$figure
    checkpoints_b <- res$checkpoint_avg
  }

  if(length(checkpoints_a) > length(checkpoints_b)){
    checkpoints_b <- c(checkpoints_b, rep(1, length(checkpoints_a) - length(checkpoints_b)))
  } else if (length(checkpoints_a) < length(checkpoints_b)){
    checkpoints_a <- c(checkpoints_a, rep(1, length(checkpoints_b) - length(checkpoints_a)))
  }
  #########
  checkpoints_diff <- checkpoints_a / checkpoints_b
  x <- seq(from = 100, to = length(checkpoints_diff) * 100, by = 100)
  length(checkpoints_diff)
  length(x)
  checkpoints <- data.frame(x, checkpoints_diff)
  
  spline_d <- as.data.frame(spline(checkpoints$x, checkpoints$checkpoints_diff))
  inset <- ggplot(checkpoints, aes(x = x, y = checkpoints_diff)) + geom_point(size = 0.8, shape = 4) +
    geom_line(data = spline_d, aes(x = x, y = y), linetype = "dashed", linewidth = 0.01) +
    labs(x = "Driving Time [s]", y = "Tree / Actuated ") + 
    theme_classic() + 
    theme(plot.title = element_text(hjust = 0.5),
          axis.title.x = element_text(size = 12),
          axis.title.y = element_text(size = 12)) +
    ylim(1, 2)

  data_tb <- tibble(x = 4750, y = 0.01, plot = list(inset))

  density <- density + 
    labs(title = title, x = x_title, y = y_title, color = "Legend") +
    theme_classic() +
    theme(legend.position = c(0.75, 0.75), legend.title = element_blank(),
          plot.title = element_text(hjust = 0.5),
          axis.title.x = element_text(size = 12),
          axis.title.y = element_text(size = 12)) +
    scale_color_manual(values = colors) +
    geom_plot(data = data_tb, aes(x, y, label = plot))
  
  fileName <- sprintf("%s-ecdf-%s.pdf", feagure_id, title)
  setwd(origin_path)
  ggsave(filename = fileName)
}

x_title <- "Driving Time [s]"
y_title_cum <- "Cumulative Density"
file_name <- "driving_time_distribution.txt"
title <-"Driving Time Cumulative Density"
N <- 20
print_ecdf_figure(path_exp1, title, x_title, y_title_cum, N, c("SUMOActuated", "CurrentTreeDvd"), 1, file_name, colors, '5A')


############################ figure 6A over time ################:

add_arrived_over_time_to_figure <- function(figure, directory_path, N, tl_method, color, total_v_count, feagure_id) {
  fit_line_a <- c()
  fit_line_r2 <- c()
  fit_line_adj_r2 <- c()
  for (i in 1:N) {
    path <- sprintf("%s/%s/%s", directory_path, i, tl_method)
    setwd(path)
    data <- read.delim("vehicles_stats.txt", sep = ",")
    d <- data[4]
    names(d)[1] <- "v"
    df <- data.frame(d$v[1:80])
    names(df)[1] <- "v"
    x <- c(1:80)
    linear_model <- lm(v ~ x, data = df)
    l_data <- summary(linear_model)
    a <- linear_model$coefficients[2]
    fit_line_a <- append(fit_line_a, as.numeric(a))
    fit_line_r2 <- append(fit_line_r2, l_data$r.squared)
    fit_line_adj_r2 <- append(fit_line_adj_r2, l_data$adj.r.squared)
    figure <- figure + geom_line(data = df, aes(x = c(1:length(v)), y = v / total_v_count, color = color))
  }
  fit_lines_df <- data.frame(fit_line_a, fit_line_r2, fit_line_adj_r2)
  write.csv(fit_lines_df, file = sprintf("D:/Nimrod/SIM2/r2/%s-%s.csv", feagure_id, tl_method), row.names = FALSE)
  return (figure)
}

print_overtime_figure <- function(path, title, x_title, y_title, N, v_count, series, colors, feagure_id) {
  
  over_time <- ggplot()
  if ("CurrentTreeDvd" %in% series) {
    over_time <- add_arrived_over_time_to_figure(over_time, path, N, "CurrentTreeDvd", "Tree 20 runs", v_count, feagure_id)
  }
  if ("SUMOActuated" %in% series) {
    over_time <- add_arrived_over_time_to_figure(over_time, path, N, "SUMOActuated", "SUMO Actuated 20 runs", v_count, feagure_id)
  }
  over_time <- over_time + 
    labs(title = title, x = x_title, y = y_title, color = "Legend") +
    scale_x_continuous(expand = c(0, 0), limits = c(0, 80)) +
    scale_y_continuous(expand = c(0, 0), limits = c(0, 1)) + 
    theme_classic() +
    theme(legend.position = c(0.8, 0.2), legend.title = element_blank(),
          plot.title = element_text(hjust = 0.5),
          axis.title.x = element_text(size = 12),
          axis.title.y = element_text(size = 12),
          axis.text = element_text(size = 10)) +
    scale_color_manual(values = colors) + 
    scale_size_manual(values = c(0.01))
  
  fileName <- sprintf("%s-over time-%s.pdf", feagure_id, title)
  setwd(origin_path)
  pdf(fileName)
  print(over_time)
  dev.off()
}

x_title <- "Simulation Iterations"
y_title <- "Cumulative Throughput Ratio"
title <-"Cumulative Throughput Ratio over time"
N <- 20
print_overtime_figure(path_exp1, title, x_title, y_title, N, v_count_100, c("SUMOActuated", "CurrentTreeDvd"), colors, '6A')


###################### Figure 6B over time ################################:
aggregate_df_to_vector <- function(df) {
  mean <- rowMeans(df)
  row_stdev <- apply(df, 1, sd)
  se <- row_stdev / sqrt(ncol(df))
  x <- seq(from = 1, to = nrow(df), by = 1)
  res <- data.frame(x, mean, se)
  return (res)
}

add_cum_cost_by_iter_to_over_time_figure <- function(figure, directory_path, N, tl_method, color, feagure_id, iterations.count) {
  fit_line_a <- c()
  fit_line_r2 <- c()
  fit_line_adj_r2 <- c()
  for (i in 1:N) {
    path <- sprintf("%s/%s/%s", directory_path, i, tl_method)
    setwd(path)
    data <- read.delim("tree_cost_distribution.txt", sep = ",")
    iter <- c(data[[1]] + 1, seq(from = 1, to = iterations.count, by = 1))
    cost <- c(data[[2]], rep(0, iterations.count))
    df <- data.frame(iter, cost)
    t <- df %>%
      group_by(iter) %>%
      mutate(v = sum(cost)) %>%
      filter(cost == min(cost))
    x <- c(1:iterations.count)
    linear_model <- lm(cumsum(v) ~ iter, data = t)
    l_data <- summary(linear_model)
    a <- linear_model$coefficients[2]
    fit_line_a <- append(fit_line_a, as.numeric(a))
    fit_line_r2 <- append(fit_line_r2, l_data$r.squared)
    fit_line_adj_r2 <- append(fit_line_adj_r2, l_data$adj.r.squared)
    if (i == 1){
      all_runs_df <- data.frame(cumsum(t$v)[1:iterations.count])
    } else {
      this_df <- data.frame(cumsum(t$v)[1:iterations.count])
      col.name <- sprintf("v%s", i)
      names(this_df) <- col.name
      all_runs_df <- cbind(all_runs_df, this_df)
    }
  }
  fit_lines_df <- data.frame(fit_line_a, fit_line_r2, fit_line_adj_r2)
  write.csv(fit_lines_df, file = sprintf("D:/Nimrod/SIM2/r2/%s-%s.csv", feagure_id, tl_method), row.names = FALSE)
  res <- aggregate_df_to_vector(all_runs_df)
  
  figure<- figure + geom_line(data = res, mapping = aes(x = x, y = mean, color = color)) + 
    geom_errorbar(data = res, mapping = aes(x = x, ymin = mean - se, ymax = mean + se, color = color), width = .5) +
    geom_point(data = res, mapping = aes(x = x, y = mean, color = color), size = 1)
  return (figure)
}

print_cum_cost_overtime_figure <- function(path, title, x_title, y_title, N, series, colors, feagure_id) {
  iterations_count <- 80
  over_time <- ggplot()
  if ("CurrentTreeDvd" %in% series) {
    over_time <- add_cum_cost_by_iter_to_over_time_figure(over_time, path, N, "CurrentTreeDvd", "Tree 20 runs",
                                                         feagure_id, iterations_count)
  }
  if ("SUMOActuated" %in% series) {
    over_time <- add_cum_cost_by_iter_to_over_time_figure(over_time, path, N, "SUMOActuated", "SUMO Actuated 20 runs",
                                                         feagure_id, iterations_count)
  }
  over_time <- over_time + 
    labs(title = title, x = x_title, y = y_title, color = "Legend") +
    scale_x_continuous(expand = c(0, 0), limits = c(0, 80)) +
    scale_y_continuous(expand = c(0, 0), limits = c(0, 80000)) + 
    theme_classic() +
    theme(legend.position = c(0.8, 0.1), legend.title = element_blank(),
          plot.title = element_text(hjust = 0.5),
          axis.title.x = element_text(size = 12),
          axis.title.y = element_text(size = 12),
          axis.text = element_text(size = 10)) +
    scale_color_manual(values = colors) +
    scale_linewidth(range = c(0.0005, 0.001))
  
  fileName <- sprintf("%s-over time-%s.pdf", feagure_id, title)
  setwd(origin_path)
  ggsave(over_time, filename = fileName)
}

x_title <- "Simulation Iterations"
y_title <- "Cumulative Cost [m]"
title <-"Cumulative Cost over time"
N <- 20
print_cum_cost_overtime_figure(path_exp1, title, x_title, y_title, N, c("SUMOActuated", "CurrentTreeDvd"), colors, '6B')

################## Figure S1 trees mean count ################################:
count_trees <- function(directory_path, N, tl_method) {
  res <- NULL
  for (i in 1:N) {
    path = sprintf("%s/%s/%s", directory_path, i, tl_method)
    setwd(path)
    data <- read.delim("tree_cost_distribution.txt", sep = ",")
    res[i] <- nrow(data[2])
  }
  return (res)
}

print_trees_col_with_e_bars <- function(df, title, y_title, x_title, first_series, second_series) {
  p <- ggplot(df, aes(x = n_mean, y = method_name, color, fill = method_name), linewidth = 0.2) + 
    geom_bar(stat = "identity", color = "black", width = .6, position = "dodge") +
    geom_errorbar(aes(xmin = n_mean-se, xmax = n_mean + se), width = .2,
                  position = position_dodge(width = .9)) + 
    labs(x = x_title, y = y_title) +
    theme_classic() +
    theme(aspect.ratio = 1/2) + 
    theme(plot.title = element_text(hjust = 0.5), 
          axis.title.x = element_text(size = 12),
          axis.title.y = element_text(size = 12),
          legend.title = element_blank()) + 
    scale_fill_manual(values = c("#a832a8", "#2f99d6"), breaks = c(first_series, second_series))
  fileName <- sprintf("%s-%s.pdf", 'S1', title)
  setwd(origin_path)
  pdf(fileName)
  print(p)
  dev.off()
}

print_trees_count_mean <- function () {
  N <- 20
  trees_actuated <- count_trees(path_exp1, N, "SUMOActuated")
  trees_current_tree_dvd <- count_trees(path_exp1, N, "CurrentTreeDvd")
  datalist <- vector("list", length = 2)
  datalist <- add_meas_vector(trees_actuated, 1, datalist, "SUMO Actuated")
  datalist <- add_meas_vector(trees_current_tree_dvd, 2, datalist, "Tree")
  data_with_se <- do.call(rbind, datalist)
  print_trees_col_with_e_bars(data_with_se,
                              "Average Number of Congested Trees per Traffic Light Method",
                              "Traffic Light Method", "Average Number of Congested Trees","SUMO Actuated", "Tree")
}

add_meas_vector <- function(data, index, datalist, method_name) {
  dat <- data.frame(n_mean = mean(data),
                    se = sd(data) / sqrt(length(data)),
                    method_name = method_name)
  datalist[[index]] <- dat
  return (datalist)
}

print_trees_count_mean()

#####################
