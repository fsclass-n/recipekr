package com.recipekr.repository;

import com.recipekr.domain.Recipe;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class RecipeRepository {
    private final JdbcTemplate jdbcTemplate;

    public RecipeRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<Recipe> recipeRowMapper = (rs, rowNum) -> Recipe.builder()
            .id(rs.getLong("id"))
            .title(rs.getString("title"))
            .ingredients(rs.getString("ingredients"))
            .calories(rs.getInt("calories"))
            .healthType(rs.getString("health_type"))
            .recipeText(rs.getString("recipe_text"))
            .createdAt(rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toLocalDateTime() : null)
            .build();

    public void save(Recipe recipe) {
        String sql = "INSERT INTO recipes (title, ingredients, calories, health_type, recipe_text) VALUES (?, ?, ?, ?, ?)";
        jdbcTemplate.update(sql, recipe.getTitle(), recipe.getIngredients(), recipe.getCalories(), recipe.getHealthType(), recipe.getRecipeText());
    }

    public List<Recipe> findAll() {
        String sql = "SELECT * FROM recipes ORDER BY id DESC";
        return jdbcTemplate.query(sql, recipeRowMapper);
    }
}
