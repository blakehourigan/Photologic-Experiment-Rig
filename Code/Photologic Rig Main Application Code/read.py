import pstats

# Load the stats
p = pstats.Stats('program.prof')

# Sort the statistics by the cumulative time spent
p.sort_stats('cumulative').print_stats()

# Dump the stats to a file
with open('profile_stats.txt', 'w') as f:
    p = pstats.Stats('program.prof', stream=f)
    p.sort_stats('cumulative').print_stats()
