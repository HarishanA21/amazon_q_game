import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 150, 255)
GREEN = (100, 200, 100)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
RED = (255, 100, 100)
YELLOW = (255, 255, 100)
SKIN_COLOR = (255, 220, 177)
LIGHT_BLUE = (200, 220, 255)

# Game settings
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
INITIAL_STEP_SPEED = 0.8
MAX_STEP_SPEED = 4
STEP_SPAWN_RATE = 120
GRAB_DISTANCE = 50  # Increased grab distance

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 45
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.grabbing = False
        self.grab_step = None
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.state = "idle"
    def update(self, steps):
        # Handle input
        keys = pygame.key.get_pressed()
        
        if not self.grabbing:
            # Horizontal movement
            if keys[pygame.K_LEFT]:
                self.vel_x = -MOVE_SPEED
                self.facing_right = False
                if self.on_ground:
                    self.state = "running"
            elif keys[pygame.K_RIGHT]:
                self.vel_x = MOVE_SPEED
                self.facing_right = True
                if self.on_ground:
                    self.state = "running"
            else:
                self.vel_x = 0
                if self.on_ground:
                    self.state = "idle"
            
            # Jumping
            if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
                self.vel_y = JUMP_STRENGTH
                self.on_ground = False
                self.state = "jumping"
                
        else:
            # Climbing logic
            if keys[pygame.K_UP]:
                return self.climb_onto_step()
        
        # Apply gravity
        if not self.grabbing:
            self.vel_y += GRAVITY
            
        # Update position
        if not self.grabbing:
            self.x += self.vel_x
            self.y += self.vel_y
            
        # Keep player on screen horizontally
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        
        # Check collisions with steps
        landed_step = self.check_step_collisions(steps)
        
        # Check for grabbing opportunities (enhanced detection)
        if not self.on_ground and not self.grabbing and self.vel_y > 0:
            self.check_grab_opportunities(steps)
            
        # Update animations
        self.update_animation()
        
        return landed_step
    def check_step_collisions(self, steps):
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        
        for step in steps:
            step_rect = pygame.Rect(step.x, step.y, step.width, step.height)
            
            if player_rect.colliderect(step_rect) and self.vel_y >= 0:
                # Landing on top of step
                if self.y < step.y:
                    self.y = step.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                    self.state = "idle"
                    return step
        return None
    def check_grab_opportunities(self, steps):
        player_center_x = self.x + self.width / 2
        player_center_y = self.y + self.height / 2
        
        for step in steps:
            step_center_x = step.x + step.width / 2
            step_center_y = step.y + step.height / 2
            
            # Calculate distance to step
            distance = math.sqrt((player_center_x - step_center_x)**2 + 
                               (player_center_y - step_center_y)**2)
            
            # Enhanced grab detection - more forgiving
            vertical_distance = abs(player_center_y - step_center_y)
            horizontal_distance = abs(player_center_x - step_center_x)
            
            # Allow grabbing if player is reasonably close
            if (distance < GRAB_DISTANCE and 
                vertical_distance < 40 and 
                horizontal_distance < step.width/2 + 25 and
                self.y > step.y - 30):
                
                self.grab_step = step
                self.grabbing = True
                self.state = "grabbing"
                self.vel_x = 0
                self.vel_y = 0
                # Position player hanging from step
                self.x = step.x + step.width/2 - self.width/2
                self.y = step.y + step.height
                break
    def climb_onto_step(self):
        if self.grab_step:
            self.y = self.grab_step.y - self.height
            self.grabbing = False
            self.on_ground = True
            self.state = "idle"
            climbed_step = self.grab_step
            self.grab_step = None
            return climbed_step
        return None
    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= 8:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
    def draw(self, screen):
        # Human-like character sprite
        
        # Head
        head_x = self.x + self.width//2
        head_y = self.y + 8
        pygame.draw.circle(screen, SKIN_COLOR, (int(head_x), int(head_y)), 8)
        
        # Eyes
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(screen, BLACK, (int(head_x + eye_offset), int(head_y - 2)), 2)
        
        # Body
        body_color = GREEN
        if self.state == "jumping":
            body_color = YELLOW
        elif self.state == "grabbing":
            body_color = RED
        elif self.state == "running":
            body_color = BLUE
            
        pygame.draw.rect(screen, body_color, (self.x + 5, self.y + 16, self.width - 10, 20))
        
        # Arms
        arm_y = self.y + 20
        if self.state == "grabbing":
            # Arms reaching up
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), (self.x + 3, self.y + 5), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 3, self.y + 5), 4)
        elif self.state == "running":
            # Swinging arms
            arm_swing = math.sin(self.animation_frame * 0.8) * 8
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), 
                           (self.x + 8 + arm_swing, arm_y + 12), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 8 - arm_swing, arm_y + 12), 4)
        else:
            # Normal arms
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), (self.x + 8, arm_y + 12), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 8, arm_y + 12), 4)
        
        # Legs
        leg_y = self.y + 36
        if self.state == "running":
            # Running legs animation
            leg_swing = math.sin(self.animation_frame) * 10
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), 
                           (self.x + 8 + leg_swing, leg_y + 15), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 8 - leg_swing, leg_y + 15), 4)
        elif self.state == "jumping":
            # Bent legs for jumping
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), (self.x + 12, leg_y + 10), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 12, leg_y + 10), 4)
        else:
            # Standing legs
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), (self.x + 8, leg_y + 15), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 8, leg_y + 15), 4)

class Step:
    def __init__(self, x, y, width, column, step_type="normal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.column = column
        self.step_type = step_type
        self.color = self.get_color()
    def get_color(self):
        if self.step_type == "easy":
            return (101, 67, 33)  # Darker brown for easy steps
        elif self.step_type == "small":
            return (160, 82, 45)  # Lighter brown for small steps
        else:
            return BROWN
    def update(self, speed):
        self.y -= speed
    def draw(self, screen):
        # Main step
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        
        # Add texture
        for i in range(0, self.width, 15):
            pygame.draw.line(screen, BLACK, (self.x + i, self.y), (self.x + i, self.y + self.height), 1)

class StepGenerator:
    def __init__(self):
        self.spawn_timer = 0
        self.difficulty = 1.0
        self.last_column = -1
    def update(self, steps, game_time):
        # Progressive difficulty
        time_factor = min(game_time / 15000, 1.0)  # Max difficulty after 4 minutes
        self.difficulty = 1 + (time_factor * 2)
        
        self.spawn_timer += 1
        spawn_rate = max(40, int(STEP_SPAWN_RATE / self.difficulty))
        
        if self.spawn_timer >= spawn_rate:
            self.spawn_step(steps, game_time)
            self.spawn_timer = 0
    def spawn_step(self, steps, game_time):
        # Avoid same column consecutively
        available_columns = [0, 1, 2]
        if self.last_column != -1 and len(available_columns) > 1:
            available_columns.remove(self.last_column)
        
        column = random.choice(available_columns)
        self.last_column = column
        
        # Progressive step size difficulty - starts with 90% easy steps
        time_factor = min(game_time / 15000, 1.0)
        easy_probability = 0.9 - (0.4 * time_factor)  # 90% to 50%
        
        rand_val = random.random()
        if rand_val < easy_probability:
            # Easy step (large)
            step_width = random.randint(120, 160)
            step_type = "easy"
        elif rand_val < easy_probability + 0.3:
            # Normal step
            step_width = random.randint(80, 120)
            step_type = "normal"
        else:
            # Small step (challenging)
            step_width = random.randint(50, 80)
            step_type = "small"
        
        # Position based on column
        if column == 0:  # Left wall
            x = 50
        elif column == 1:  # Middle
            base_x = SCREEN_WIDTH // 2 - step_width // 2
            variation = min(60, step_width // 4)
            x = base_x + random.randint(-variation, variation)
            x = max(60, min(SCREEN_WIDTH - step_width - 60, x))
        else:  # Right wall
            x = SCREEN_WIDTH - 50 - step_width
        
        y = SCREEN_HEIGHT + 20
        
        new_step = Step(x, y, step_width, column, step_type)
        steps.append(new_step)

class Plane:
    def __init__(self):
        self.x = -120
        self.y = 80
        self.width = 80
        self.height = 30
        self.speed = 2.5
        self.active = False
        self.player_dropped = False
    def update(self):
        if self.active:
            self.x += self.speed
    def should_drop_player(self):
        return self.x > SCREEN_WIDTH // 2 - 50 and not self.player_dropped
    def draw(self, screen):
        if self.active and self.x < SCREEN_WIDTH + 100:
            # Plane body
            pygame.draw.ellipse(screen, GRAY, (self.x, self.y, self.width, self.height))
            # Wings
            pygame.draw.rect(screen, GRAY, (self.x + 20, self.y - 8, 40, 8))
            pygame.draw.rect(screen, GRAY, (self.x + 20, self.y + self.height, 40, 8))
            # Tail
            pygame.draw.polygon(screen, GRAY, [
                (self.x + self.width, self.y + self.height//2),
                (self.x + self.width + 15, self.y + self.height//2 - 8),
                (self.x + self.width + 15, self.y + self.height//2 + 8)
            ])

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Working Survival Points Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "start"  # start, intro, playing, game_over
        self.score = 0
        self.game_time = 0
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        # Game objects
        self.player = None
        self.plane = Plane()
        self.steps = []
        self.step_generator = StepGenerator()
        self.step_speed = INITIAL_STEP_SPEED
        self.last_step_landed = None
        self.parachute_timer = 0
    def reset_game(self):
        self.steps = []
        self.score = 0
        self.game_time = 0
        self.step_speed = INITIAL_STEP_SPEED
        self.step_generator = StepGenerator()
        self.last_step_landed = None
        self.parachute_timer = 0
        
        # Start intro sequence
        self.game_state = "intro"
        self.plane = Plane()
        self.plane.active = True
        self.plane.player_dropped = False
        self.player = None
        
        # Create initial large landing platform
        initial_step = Step(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 120, 200, 1, "easy")
        self.steps.append(initial_step)
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == "start" and event.key == pygame.K_SPACE:
                    self.reset_game()
                elif self.game_state == "game_over" and event.key == pygame.K_SPACE:
                    self.game_state = "start"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "start":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.reset_game()
    def update(self):
        if self.game_state == "intro":
            self.plane.update()
            
            # Drop player from plane
            if self.plane.should_drop_player():
                self.player = Player(self.plane.x + 40, self.plane.y + 30)
                self.player.vel_y = 1.5  # Slow fall
                self.parachute_timer = 100  # About 1.7 seconds
                self.plane.player_dropped = True
            
            # Handle parachute descent
            if self.player:
                if self.parachute_timer > 0:
                    self.parachute_timer -= 1
                    self.player.y += 1.5  # Controlled descent
                    # Keep player centered over landing platform
                    target_x = SCREEN_WIDTH // 2 - self.player.width // 2
                    if abs(self.player.x - target_x) > 5:
                        self.player.x += (target_x - self.player.x) * 0.1
                else:
                    # Land on platform and start game
                    for step in self.steps:
                        if step.y > SCREEN_HEIGHT - 150:
                            self.player.y = step.y - self.player.height
                            self.player.x = step.x + step.width/2 - self.player.width/2
                            self.player.on_ground = True
                            self.player.vel_y = 0
                            self.game_state = "playing"
                            break
                
        elif self.game_state == "playing":
            self.game_time += 1
            
            # Update step speed
            time_factor = min(self.game_time / 10000, 1.0)
            self.step_speed = INITIAL_STEP_SPEED + (MAX_STEP_SPEED - INITIAL_STEP_SPEED) * time_factor
            
            # Update player
            landed_step = self.player.update(self.steps)
            if landed_step and landed_step != self.last_step_landed:
                self.score += 1
                self.last_step_landed = landed_step
            
            # Update steps
            for step in self.steps[:]:
                step.update(self.step_speed)
                if step.y < -step.height:
                    self.steps.remove(step)
            
            # Generate new steps
            self.step_generator.update(self.steps, self.game_time)
            
            # Check game over
            if self.player.y > SCREEN_HEIGHT:
                self.game_state = "game_over"
    def draw_background(self):
        # Gradient sky
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(LIGHT_BLUE[0] * (1 - color_ratio) + WHITE[0] * color_ratio)
            g = int(LIGHT_BLUE[1] * (1 - color_ratio) + WHITE[1] * color_ratio)
            b = int(LIGHT_BLUE[2] * (1 - color_ratio) + WHITE[2] * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    def draw_start_screen(self):
        self.draw_background()
        
        # Title
        title_text = self.big_font.render("Q JUMP", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(title_text, title_rect)
        
        # Start button
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
        pygame.draw.rect(self.screen, GREEN, button_rect)
        pygame.draw.rect(self.screen, BLACK, button_rect, 3)
        
        button_text = self.font.render("Start Game", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, button_text_rect)
        
        # Instructions
        instructions = [
            "🎮 Arrow keys: Move and jump",
            "🤏 Get close to steps to grab automatically",
            "⬆️ UP key: Climb onto grabbed steps",
            "🎯 Starts easy (90% large steps), gets harder!",
            "🏆 Survive as long as possible!"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100 + i * 35))
            self.screen.blit(text, text_rect)
    def draw_game_over_screen(self):
        self.draw_background()
        
        # Game Over
        game_over_text = self.big_font.render("Game Over", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Score
        score_text = self.font.render(f"Final Score: {self.score} steps", True, BLACK)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(score_text, score_rect)
        
        # Performance message
        if self.score >= 50:
            perf_msg = "🏆 Excellent! Master climber!"
        elif self.score >= 30:
            perf_msg = "🥈 Great job! Skilled player!"
        elif self.score >= 15:
            perf_msg = "🥉 Not bad! Keep practicing!"
        else:
            perf_msg = "💪 Keep trying! You'll improve!"
            
        perf_text = self.font.render(perf_msg, True, BLUE)
        perf_rect = perf_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
        self.screen.blit(perf_text, perf_rect)
        
        # Restart
        restart_text = self.font.render("Press SPACE to return to menu", True, BLACK)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
        self.screen.blit(restart_text, restart_rect)
    def draw_game(self):
        self.draw_background()
        
        # Draw walls
        pygame.draw.rect(self.screen, GRAY, (0, 0, 50, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH - 50, 0, 50, SCREEN_HEIGHT))
        
        # Draw steps
        for step in self.steps:
            step.draw(self.screen)
        
        # Draw plane during intro
        if self.game_state == "intro":
            self.plane.draw(self.screen)
            
            # Draw parachute
            if self.player and self.parachute_timer > 0:
                parachute_x = self.player.x + self.player.width//2
                parachute_y = self.player.y - 40
                pygame.draw.arc(self.screen, RED, (parachute_x - 25, parachute_y, 50, 30), 0, math.pi, 4)
                # Parachute lines
                pygame.draw.line(self.screen, BLACK, (parachute_x - 20, parachute_y + 15), 
                               (self.player.x + 5, self.player.y), 2)
                pygame.draw.line(self.screen, BLACK, (parachute_x + 20, parachute_y + 15), 
                               (self.player.x + self.player.width - 5, self.player.y), 2)
        
        # Draw player
        if self.player:
            self.player.draw(self.screen)
        
        # UI
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        score_bg = pygame.Rect(5, 5, score_text.get_width() + 10, 35)
        pygame.draw.rect(self.screen, WHITE, score_bg)
        pygame.draw.rect(self.screen, BLACK, score_bg, 2)
        self.screen.blit(score_text, (10, 10))
        
        speed_text = self.font.render(f"Speed: {self.step_speed:.1f}x", True, BLACK)
        speed_bg = pygame.Rect(5, 45, speed_text.get_width() + 10, 35)
        pygame.draw.rect(self.screen, WHITE, speed_bg)
        pygame.draw.rect(self.screen, BLACK, speed_bg, 2)
        self.screen.blit(speed_text, (10, 50))
        
        # Difficulty indicator
        difficulty = int(self.step_generator.difficulty)
        diff_text = self.font.render(f"Difficulty: {difficulty}/3", True, BLACK)
        diff_bg = pygame.Rect(5, 85, diff_text.get_width() + 10, 35)
        pygame.draw.rect(self.screen, WHITE, diff_bg)
        pygame.draw.rect(self.screen, BLACK, diff_bg, 2)
        self.screen.blit(diff_text, (10, 90))
        
        # Grabbing instruction
        if self.player and self.player.grabbing:
            grab_text = self.big_font.render("Press UP to climb!", True, RED)
            grab_bg = pygame.Rect(SCREEN_WIDTH//2 - grab_text.get_width()//2 - 10, 80, 
                                grab_text.get_width() + 20, grab_text.get_height() + 10)
            pygame.draw.rect(self.screen, WHITE, grab_bg)
            pygame.draw.rect(self.screen, RED, grab_bg, 3)
            grab_rect = grab_text.get_rect(center=(SCREEN_WIDTH//2, 90))
            self.screen.blit(grab_text, grab_rect)
    def draw(self):
        if self.game_state == "start":
            self.draw_start_screen()
        elif self.game_state in ["intro", "playing"]:
            self.draw_game()
        elif self.game_state == "game_over":
            self.draw_game_over_screen()
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
