library("dplyr")
library("ggplot2")
library("ggsci")
library(viridis)
library(plotrix)
library(RColorBrewer)
library("wesanderson")
#
my_colors1 <- RColorBrewer::brewer.pal(6, "Set1")
my_colors2 <- wes_palette("Darjeeling1", 5, type = "discrete")
#
two_images = theme(
    legend.position = "top", # "none", 
    axis.title.x    = element_text(size = 16),
    axis.text.x     = element_text(size = 14),
    axis.text.y     = element_text(size = 14),
    axis.title.y    = element_text(size = 16),
    legend.text     = element_text(size = 14),
    axis.title      = element_text(size = 16),
    legend.title    = element_text(size = 16))
# Erase the workplace
# rm(list = ls())
#
# Prepare the dataset adding the source position as factor
data_prev <- data.table::fread("databases/Summary.csv")
data_new <- data.table::fread("databases/Strategy4.csv")
data = bind_rows(data_prev, data_new) 
#
factors <- factor(paste(
    as.character(data$source_pos_x),
    as.character(data$source_pos_y),
    sep = "-"
))
factors2 <-
    factor(paste(as.character(
        round(data$initial_height_1, digits = 0)
    ),
    as.character(
        round(data$initial_height_2, digits = 0)
    ),
    sep = "-"))
#
data = mutate(data, Match = grepl("3",factors2))
#
levels(factors)  <-
    c("southwest", "southeast", "northwest", "northeast")
#
data <- mutate(data, source_pos = factors)
#
data <- select(
    data,
    Strategy,
    source_pos,
    Match,
    firstDV,
    firstDT,
    probable_time,
    best_value,
    best_value_time,
    dist_prob2source,
    dist_best2source,
    initial_height_1,
    initial_height_2
)
#
sep_Data <- split(data, list(data$Strategy, data$Match))
nombres  <- names(sep_Data)
#
# Show matches and no matches 
for (e in seq(sep_Data)) {
    print(sprintf(">>> %s", nombres[e]))
    completos   <- complete.cases(select(sep_Data[[nombres[e]]], "firstDT"))
    incompletos <- !complete.cases(select(sep_Data[[nombres[e]]], "firstDT"))
    print(sprintf(
        "Completos = %i  -- Incompletos = %i",
        sum(completos),
        sum(incompletos)
    ))
}
#
completos      <- complete.cases(select(data, 'firstDT'))
cdata          <- data[completos, ]
cdata$Strategy <- as.factor(cdata$Strategy)
cdata          <- mutate(cdata, rtime = best_value - firstDV)
#

#-----------------------------------------------------------------
#
s <-
    ggplot(cdata,
           aes(
               x = dist_best2source,
               y = best_value,
               color = Strategy
           )) +
    facet_wrap( ~ Match, scale = "free", labeller = label_both) +
    theme(strip.text.x = element_text(size = 14)) +
    geom_point(size = 1.5,
               shape = 16) + # colour = "blue",
    labs(x = "Distance to the source [m]", 
         y = "Highest pollutant measured [ppm]") +
    #two_images + scale_color_manual(values=my_colors2)
    two_images + scale_color_lancet() # scale_fill_aaas() 
print(s)

#------------------------------------------------------------------
#
strategy15 = filter(cdata, Strategy == 1 )
strategy15[, "Strategy"] <- factor(1.5)
strategy15[, "dist_best2source"] <- strategy15[, "dist_prob2source"]
#
# Boxplots dist_best2source
data4num <- bind_rows(strategy15, cdata)  %>%
    group_by(Match, Strategy) %>%
    summarise(
        n       = n(),
        q3      = quantile(dist_best2source, 0.75),
        iqr     = IQR(dist_best2source),
        lab_pos = max(dist_best2source)
    )
p <- bind_rows(strategy15, cdata) %>% 
    ggplot(aes(y = dist_best2source, 
               #x = Match, 
               x = reorder(Match, dist_best2source, FUN = median),
               fill = Strategy)) +
    stat_boxplot(geom     = "errorbar",
                 position =  position_dodge2(width    = 0.75,
                                             preserve = "single")) +
    geom_boxplot(position =  position_dodge(width = 0.75)) +
    #facet_wrap(~ Match, scale = "free") +
    geom_text(
        data = data4num,
        aes(
            x     = Match,
            y     = lab_pos,
            label = paste0("n=", n, "\n")
        ),
        position = position_dodge2(width = 0.75, preserve = "single"),
        size = 4
    ) + 
    labs(x = "Matches the height of the source",
         y = "Distance to the source [m]") +
    two_images + scale_color_lancet() + ylim(0,425)
print(p)

#------------------------------------------------------------------
#
# Boxplot firstDT, diff_value, best_value, best_value_time
titles = c("Time until first detection [sec]", 
           "Improvement of the result [ppm]",
           "Highest measurement [ppm]",
           "Time to highest measurement [sec]")
vars = c("firstDT", "rtime", "best_value", "best_value_time")
pl = 2
#
data4num <- cdata %>%
    group_by(Match, Strategy) %>%
    summarise(
        n   = n(),
        q3  = quantile(rtime, 0.75),
        iqr = IQR(rtime),
        lab_pos = max(rtime)
    )
p <-
    ggplot(cdata, aes(y = rtime, 
                      x = reorder(Match, dist_best2source, FUN = median),
                      fill = Strategy)) +
    stat_boxplot(geom     = "errorbar",
                 position =  position_dodge2(width = 0.75, 
                                             preserve = "single")) +
    geom_boxplot(position =  position_dodge(width = 0.75)) +
    #facet_wrap( ~ Match, scale = "free", labeller = label_both) +
    geom_text(
        data = data4num,
        aes(
            x = Match,
            y = lab_pos,
            label = paste0("n=", n, "\n")
        ),
        position = position_dodge2(width = 0.75, preserve = "single"),
        size = 4
    ) +
    labs(x = "Matches the height of the source", 
         y = titles[pl]) +
    two_images + scale_color_lancet()# + ylim(0,32)
print(p)

#------------------------------------------------------------------
# Summary data
select(cdata,
       Strategy,
       Match,
       dist_best2source,
       firstDT,
       rtime,
       best_value,
       best_value_time) %>%
    filter(Match == TRUE) %>%
    group_by(Strategy, Match) %>%
    summarise(
        min = min(dist_best2source),
        Q1 = quantile(dist_best2source, c(0.25)),
        median = median(dist_best2source),
        mean = mean(dist_best2source),
        Q3 = quantile(dist_best2source, c(0.75)),
        max = max(dist_best2source),
        sd = sd(dist_best2source)
    )
#------------------------------------------------------------------
#
# For time analysis
times <- data.table::fread("databases/Time4Stages.csv")
times$Strategy = as.factor(times$Strategy)
times$Stage = as.factor(times$Stage)
s <-
    ggplot(times,
           aes(
               x = Stage,
               y = time,
               fill = Strategy
           )) +
    #facet_wrap( ~ Stage, scale = "free", labeller = label_both) +
    geom_boxplot() +
    theme(strip.text.x = element_text(size = 14)) +
    labs(x = "Stage of the simulation", 
         y = "Time per loop [sec]") +
    #two_images + scale_color_manual(values=my_colors2)
    two_images + scale_color_lancet() # scale_fill_aaas() 
print(s)

times %>% group_by(Stage, Strategy) %>%
    summarise(
        min = min(time),
        Q1 = quantile(time, c(0.25)),
        median = median(time),
        mean = mean(time),
        Q3 = quantile(time, c(0.75)),
        max = max(time),
        sd = sd(time)
    )

