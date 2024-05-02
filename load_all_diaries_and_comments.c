#include <stdio.h>
#include <string.h>
#include <dirent.h>

#define DIR_PATH "C:/Users/IWMAI/OneDrive/Personal-Diaries/"

char *read_single_file(char *dir_name, char *file_name)
{
    // load file name
    char df_name[256];
    strcpy(df_name, DIR_PATH);
    strcat(df_name, dir_name);
    strcat(df_name, file_name);
    // Read the content
    static char ans[8192];
    memset(ans, 0, sizeof(ans));
    FILE *fp;
    fp = fopen(df_name, "r");
    if (fp == NULL) {
        printf("Failed to open file %s\n", df_name);
        return ans;
        // exit(-1);
    }
    char s[100];
    while (1)
    {
        fscanf(fp, "%99s", s);
        strcat(ans, s);
        if (feof(fp))
            break;
    }
    return ans;
}

int main()
/*Write all the diaries and comments into a single file*/
{
    DIR *d;
    struct dirent *dir;
    d = opendir(DIR_PATH); // Opens the current directory
    FILE *fp;
    fp = fopen("test.txt", "w");

    if (d)
    {
        while ((dir = readdir(d)) != NULL)
        {
            fprintf(fp, "%s\n", read_single_file(dir->d_name, "/diary.txt"));
            // we do not guarantee that there is a comment file for each diary
            if (read_single_file(dir->d_name, "/comment.txt")[0] != '\0') continue;
            fprintf(fp, "%s\n\n", read_single_file(dir->d_name, "/comment.txt"));
        }
        closedir(d);
    } else {
        printf("Failed to open directory\n");
        return -1;
    }
    fclose(fp);

    return 0;
}